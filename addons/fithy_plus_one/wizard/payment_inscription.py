# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class PaymentInscriptionWz(models.TransientModel):
    _name = 'payment.inscription.wz'
    _description = 'Wizard para facturación de inscripción'

    saving_id = fields.Many2one(
        'account.saving',
        string='Plan de Ahorro',
        required=True,
        domain=[('state', '=', 'open')]
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        related='saving_id.partner_id',
        store=True,
        readonly=True
    )
    
    inscription_line_id = fields.Many2one(
        'account.saving.lines',
        string='Línea de Inscripción',
        domain=[('number', '=', 0)],
        compute='_compute_inscription_line',
        store=True
    )
    
    inscription_amount = fields.Monetary(
        string='Monto de Inscripción',
        related='inscription_line_id.serv_inscription_amount',
        store=True,
        readonly=True
    )
    
    paid_amount = fields.Monetary(
        string='Monto Pagado',
        compute='_compute_paid_amount',
        store=True,
        readonly=True
    )
    
    pending_amount = fields.Monetary(
        string='Monto Pendiente',
        compute='_compute_pending_amount',
        store=True,
        readonly=True
    )
    
    payment_amount = fields.Monetary(
        string='Monto a Pagar',
        required=True,
        default=0.0
    )
    
    payment_date = fields.Date(
        string='Fecha de Pago',
        default=fields.Date.context_today,
        required=True
    )
    
    deposit_date = fields.Date(
        string='Fecha de Depósito',
        default=fields.Date.context_today
    )
    
    payment_journal_id = fields.Many2one(
        'account.journal',
        string='Diario de Pago',
        required=True,
        domain=[('type', 'in', ['bank', 'cash'])]
    )
    
    payment_method_id = fields.Many2one(
        'account.payment.method',
        string='Método de Pago',
        required=True
    )
    
    ref = fields.Char(
        string='Referencia',
        required=True,
        default=lambda self: self._get_default_ref()
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        related='saving_id.currency_id',
        readonly=True
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        related='saving_id.company_id',
        readonly=True
    )
    
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('done', 'Procesado'),
        ('cancel', 'Cancelado')
    ], string='Estado', default='draft')
    
    @api.depends('saving_id')
    def _compute_inscription_line(self):
        for record in self:
            if record.saving_id:
                inscription_line = record.saving_id.line_ids.filtered(
                    lambda x: x.number == 0 and x.serv_inscription_amount > 0
                )
                record.inscription_line_id = inscription_line[:1].id if inscription_line else False
            else:
                record.inscription_line_id = False
    
    @api.depends('inscription_line_id')
    def _compute_paid_amount(self):
        for record in self:
            if record.inscription_line_id:
                # Obtener el valor actual de pagos directamente desde la BD
                query = """
                    SELECT COALESCE(pagos, 0) 
                    FROM account_saving_lines 
                    WHERE id = %s
                """
                self.env.cr.execute(query, (record.inscription_line_id.id,))
                result = self.env.cr.fetchone()
                record.paid_amount = result[0] if result else 0.0
            else:
                record.paid_amount = 0.0
    
    @api.depends('inscription_amount', 'paid_amount')
    def _compute_pending_amount(self):
        for record in self:
            record.pending_amount = record.inscription_amount - record.paid_amount
    
    def _get_default_ref(self):
        return self.env['ir.sequence'].next_by_code('payment.inscription.ref') or 'INS-PAY'
    
    @api.onchange('saving_id')
    def _onchange_saving_id(self):
        if self.saving_id:
            inscription_line = self.saving_id.line_ids.filtered(
                lambda x: x.number == 0 and x.serv_inscription_amount > 0
            )
            if inscription_line:
                self.inscription_line_id = inscription_line[:1].id
                # Recalcular el paid_amount
                self._compute_paid_amount()
                if self.pending_amount > (self.pending_amount * 0.50) and self.paid_amount <= 0:
                    self.payment_amount = self.pending_amount * 0.50
                else:
                    self.payment_amount = self.pending_amount
            else:
                self.inscription_line_id = False
                self.payment_amount = 0.0
            
            self.ref = f"INS-{self.saving_id.name}-{fields.Date.context_today(self)}"
    
    @api.onchange('payment_journal_id')
    def _onchange_payment_journal_id(self):
        if self.payment_journal_id:
            payment_methods = self.payment_journal_id.inbound_payment_method_line_ids
            if payment_methods:
                self.payment_method_id = payment_methods[0].payment_method_id
            else:
                self.payment_method_id = False
    
    def action_validate(self):
        self.ensure_one()
        
        if not self.saving_id:
            raise ValidationError(_("Debe seleccionar un plan de ahorro."))
        
        if not self.inscription_line_id:
            raise ValidationError(_("No se encontró una línea de inscripción en el plan."))
        
        if self.inscription_amount <= 0:
            raise ValidationError(_("El monto de inscripción debe ser mayor a cero."))
        
        if self.payment_amount <= 0:
            raise ValidationError(_("El monto a pagar debe ser mayor a cero."))
        
        if self.payment_amount > self.pending_amount:
            raise ValidationError(
                _("El monto a pagar (%.2f) no puede ser mayor al monto pendiente (%.2f).") % 
                (self.payment_amount, self.pending_amount)
            )
        
        if not self.payment_journal_id:
            raise ValidationError(_("Debe seleccionar un diario de pago."))
        
        if not self.payment_method_id:
            raise ValidationError(_("Debe seleccionar un método de pago."))
        
        if not self.ref:
            raise ValidationError(_("Debe ingresar una referencia."))
        
        return True
    
    def action_process(self):
        self.ensure_one()

        id_pa,ins,pa = self._get_data_inscription()
        
        self.action_validate()
        
        try:
            invoice = self._create_inscription_invoice()
            payment = self._create_payment(invoice)
            
            # self.inscription_line_id.write({
            #     # 'invoice_id': invoice.id,
            #     'enabled_for_invoice': False
            # })
            
            # Crear registro en account.saving.line.payment
            self._create_saving_line_payment(payment)
            
           
            
            self._create_historic_record(invoice, payment)
            self.state = 'done'

             # ACTUALIZAR DIRECTAMENTE CON SQL LA CUOTA CERO
            self._update_inscription_line_sql()

            self._update_inscription_with_sql(id_pa,ins,pa)
            
            return {
                'type': 'ir.actions.act_window',
                'name': _('Factura de Inscripción'),
                'res_model': 'account.move',
                'res_id': invoice.id,
                'view_mode': 'form',
                'target': 'current',
            }
            
        except Exception as e:
            _logger.error("Error procesando inscripción: %s", str(e))
            raise ValidationError(_("Error al procesar la inscripción: %s") % str(e))
    
    
    def _get_data_inscription(self):

        self.ensure_one()
        
        line_id = self.inscription_line_id.id
        total_inscripcion = self.inscription_amount

        query_get_pagos = """
            SELECT COALESCE(pagos, 0) 
            FROM account_saving_lines 
            WHERE id = %s
        """
        self.env.cr.execute(query_get_pagos, (line_id,))
        result = self.env.cr.fetchone()
        pagos_actual = result[0]
        
        _logger.info("=== VALOR OBTENIDO DE LA BD ===")
        _logger.info("Pagos actual: %s", pagos_actual)
        
        return line_id,total_inscripcion,pagos_actual
    

    def _update_inscription_with_sql(self,id_line,inscrip,pagos_act):

        nuevo_pagado = pagos_act + self.payment_amount
        nuevo_pendiente = inscrip - nuevo_pagado

        if nuevo_pendiente < 0:
            nuevo_pendiente = 0.0
        
        # Determinar estado
        if nuevo_pendiente <= 0.01:
            estado_pago = 'pagado'
            remanente = 0.0
        else:
            estado_pago = 'pendiente'
            remanente = nuevo_pendiente

        query = f"""
            UPDATE account_saving_lines 
            SET 
                pagos = {nuevo_pagado},
                pendiente = {nuevo_pendiente},
                estado_pago = '{estado_pago}',
                remanente = {remanente}
            WHERE id = {id_line}
        """
        print('==============================',query)
        
        self.env.cr.execute(query)
        
        _logger.info("✅ Cuota cero actualizada con SQL correctamente")
        
        return True



    
    
    def _update_inscription_line_sql(self):
        """
        ACTUALIZAR DIRECTAMENTE CON SQL LA CUOTA CERO
        Toma el valor actual de pagos desde la BD, le suma el nuevo pago y actualiza
        """
        self.ensure_one()
        
        line_id = self.inscription_line_id.id
        total_inscripcion = self.inscription_amount
        
        # Obtener el valor actual de pagos DIRECTAMENTE desde la BD
        query_get_pagos = """
            SELECT COALESCE(pagos, 0) 
            FROM account_saving_lines 
            WHERE id = %s
        """
        self.env.cr.execute(query_get_pagos, (line_id,))
        result = self.env.cr.fetchone()
        pagos_actual = result[0]
        
        _logger.info("=== VALOR OBTENIDO DE LA BD ===")
        _logger.info("Pagos actual: %s", pagos_actual)
        
        # Sumar el nuevo pago al valor actual
        nuevo_pagado = pagos_actual + self.payment_amount
        nuevo_pendiente = total_inscripcion - nuevo_pagado
        
        if nuevo_pendiente < 0:
            nuevo_pendiente = 0.0
        
        # Determinar estado
        if nuevo_pendiente <= 0.01:
            estado_pago = 'pagado'
            remanente = 0.0
        else:
            estado_pago = 'pendiente'
            remanente = nuevo_pendiente
        
        _logger.info("=== ACTUALIZANDO CUOTA CERO CON SQL ===")
        _logger.info("Line ID: %s", line_id)
        _logger.info("Total Inscripción: %s", total_inscripcion)
        _logger.info("Pagos actual (desde BD): %s", pagos_actual)
        _logger.info("Nuevo pago: %s", self.payment_amount)
        _logger.info("Nuevo pagado: %s", nuevo_pagado)
        _logger.info("Nuevo pendiente: %s", nuevo_pendiente)
        _logger.info("Estado: %s", estado_pago)
        
        # SQL UPDATE directo con parámetros (más seguro)
        query = f"""
            UPDATE account_saving_lines 
            SET 
                pagos = {nuevo_pagado},
                pendiente = {nuevo_pendiente},
                estado_pago = '{estado_pago}',
                remanente = {remanente}
            WHERE id = {line_id}
        """
        print('==============================',query)
        
        self.env.cr.execute(query)
        
        _logger.info("✅ Cuota cero actualizada con SQL correctamente")
        
        return True
    
    def _create_inscription_invoice(self):
        self.ensure_one()
        
        inscription_product = self.saving_id.saving_plan_id.inscripcion_id
        if not inscription_product:
            raise ValidationError(_("Debe configurar un producto de inscripción en el plan de ahorro."))
        
        account_receivable = self._get_account_adjudicada()
        if not account_receivable:
            raise ValidationError(_("No se pudo determinar la cuenta adjudicada."))
        
        base_amount = self.inscription_line_id.calculate_base_amount(
            self.payment_amount, 
            inscription_product.taxes_id
        )

        service_id = self.saving_id.saving_plan_id.inscripcion_id

        invoice_line_vals = []

        invoice_line_vals.append((0, 0, {
            "product_id": service_id.id,
            "name": service_id.name,
            "quantity": 1,
            "price_unit": base_amount,
            # "analytic_account_id": brw_each.saving_id.analytic_account_id and brw_each.saving_id.analytic_account_id.id or False,
            "tax_ids": [(6, 0,
                            service_id.taxes_id and service_id.taxes_id.ids or [])],
        }))
        
        # invoice_line_vals += [(0, 0, {
        #     'product_id': inscription_product.id,
        #     'name': f"Inscripción Plan de Ahorro {self.saving_id.name}",
        #     'quantity': 1,
        #     'price_unit': base_amount,
        #     'tax_ids': [(6, 0, inscription_product.taxes_id.ids or [])],
        #     'account_id': self.saving_id.property_account_receivable_id.id,
        # })]
        
        invoice_vals = {
            'partner_id': self.partner_id.id,
            'move_type': 'out_invoice',
            'date': self.payment_date,
            'invoice_date': self.payment_date,
            'journal_id': self.saving_id.journal_id.id,
            'company_id': self.company_id.id,
            'currency_id': self.currency_id.id,
            'saving_line_id': self.inscription_line_id.id,
            'saving_id': self.saving_id.id,
            'l10n_latam_document_type_id': self.saving_id.document_type_id.id,
            'l10n_latam_use_documents': True,
            'state': 'draft',
            'l10n_ec_sri_payment_id': self.env.ref("l10n_ec.P1").id,
            'is_credit_sale': self.saving_id.is_credit_sale,
            'is_credit_bank': self.saving_id.is_credit_bank,
            'is_direct': self.saving_id.is_direct,
            'is_galarplan': self.saving_id.is_galarplan,
            'invoice_line_ids': invoice_line_vals,
        }
        
        invoice = self.env['account.move'].create(invoice_vals)
        
        # for line in invoice.line_ids:
        #     if line.account_id.reconcile:
        #         line.account_id = account_receivable.id
        
        invoice.action_post()
        
        return invoice
    
    def _get_account_adjudicada(self):
        self.ensure_one()
        
        account = False
        
        if self.saving_id and self.saving_id.property_account_adjudicate_id:
            account = self.saving_id.property_account_adjudicate_id
            _logger.info("*** CUENTA ADJUDICADA DEL PLAN: %s (ID: %s)", 
                        account.name, account.id)
            return account
        
        if self.partner_id and self.partner_id.propoerty_account_adjudicated_id:
            account = self.partner_id.propoerty_account_adjudicated_id
            _logger.info("*** CUENTA ADJUDICADA DEL PARTNER: %s (ID: %s)", 
                        account.name, account.id)
            return account
        
        if self.saving_id and self.saving_id.property_account_receivable_id:
            account = self.saving_id.property_account_receivable_id
            _logger.info("*** CUENTA POR COBRAR DEL PLAN: %s (ID: %s)", 
                        account.name, account.id)
            return account
        
        if self.partner_id and self.partner_id.property_account_receivable_id:
            account = self.partner_id.property_account_receivable_id
            _logger.info("*** CUENTA POR COBRAR DEL PARTNER: %s (ID: %s)", 
                        account.name, account.id)
            return account
        
        return account
    
    def _create_payment(self, invoice):
        self.ensure_one()
        
        account_receivable = self._get_account_adjudicada()
        
        if not account_receivable:
            raise ValidationError(_("No se encontró la cuenta adjudicada."))
        
        payment_vals = {
            'date': self.payment_date,
            'journal_id': self.payment_journal_id.id,
            'saving_id': self.saving_id.id,
            'payment_method_id': self.payment_method_id.id,
            'company_id': self.company_id.id,
            'amount': self.payment_amount,
            'currency_id': self.currency_id.id,
            'partner_type': 'customer',
            'partner_id': self.partner_id.id,
            'ref': self.ref or f"INS-{self.saving_id.name}",
            'state': 'draft',
        }
        
        payment = self.env['account.payment'].create(payment_vals)
        
        for line in payment.line_ids.filtered(lambda l: l.account_id == payment.partner_id.property_account_receivable_id):
            # line.account_id = self.saving_id.property_account_receivable_id  # Usa la cuenta configurada en el cliente
              line.account_id = self.saving_id.property_account_receivable_id


        # for line in payment.line_ids:
        #     if line.account_id.reconcile:
        #         line.account_id = account_receivable.id
        #         line.partner_id = self.partner_id.id
        
        payment.action_post()
        
        payment.message_post(
            body=f'PAGO DE INSCRIPCIÓN - PLAN: {self.saving_id.name}',
            subject="Pago de Inscripción",
            message_type="notification",
            subtype_xmlid="mail.mt_note"
        )
        
        return payment
    
    def _create_saving_line_payment(self, payment):
        self.ensure_one()
        
        # Calcular el nuevo pendiente después de este pago
        nuevo_pendiente = self.pending_amount - self.payment_amount
        
        if nuevo_pendiente < 0:
            nuevo_pendiente = 0.0
        
        payment_line_vals = {
            'saving_id': self.saving_id.id,
            'saving_line_id': self.inscription_line_id.id,
            'number': 0,
            'date': self.payment_date,
            'payment_id': payment.id,
            'aplicado': self.payment_amount,
            'pendiente': nuevo_pendiente,
            'type': 'payment',
            'reconciled': True,
        }
        
        # payment_line = self.env['account.saving.line.payment'].create(payment_line_vals)
        
        _logger.info("=== REGISTRO DE PAGO CREADO PARA CUOTA CERO ===")
        _logger.info("Línea de inscripción ID: %s", self.inscription_line_id.id)
        _logger.info("Monto aplicado: %s", self.payment_amount)
        _logger.info("Nuevo pendiente: %s", nuevo_pendiente)
        
        # return payment_line
        return True
    
    def _reconcile_invoice_payment(self, invoice, payment):
        self.ensure_one()
        
        try:
            account_receivable = self._get_account_adjudicada()
            
            if not account_receivable:
                raise ValidationError(_("No se pudo determinar la cuenta adjudicada."))
            
            _logger.info("=== CONCILIANDO CON CUENTA ADJUDICADA: %s (ID: %s) ===", 
                        account_receivable.name, account_receivable.id)
            
            for line in invoice.line_ids:
                if line.account_id.reconcile and line.account_id.id != account_receivable.id:
                    line.account_id = account_receivable.id
            
            for line in payment.move_id.line_ids:
                if line.account_id.reconcile and line.account_id.id != account_receivable.id:
                    line.account_id = account_receivable.id
            
            invoice_lines = invoice.line_ids.filtered(
                lambda line: line.account_id.reconcile and abs(line.amount_residual) > 0.01
            )
            
            payment_lines = payment.move_id.line_ids.filtered(
                lambda line: line.account_id.reconcile and abs(line.amount_residual) > 0.01
            )
            
            if invoice_lines and payment_lines:
                lines_to_reconcile = invoice_lines + payment_lines
                lines_to_reconcile.reconcile()
                _logger.info("✅ Conciliación exitosa")
                return True
            
            all_invoice_lines = invoice.line_ids.filtered(lambda l: abs(l.amount_residual) > 0.01)
            all_payment_lines = payment.move_id.line_ids.filtered(lambda l: abs(l.amount_residual) > 0.01)
            
            if all_invoice_lines and all_payment_lines:
                for line in all_invoice_lines:
                    line.account_id = account_receivable.id
                for line in all_payment_lines:
                    line.account_id = account_receivable.id
                
                all_lines = all_invoice_lines + all_payment_lines
                all_lines.reconcile()
                _logger.info("✅ Conciliación exitosa con todas las líneas")
                return True
            
            raise ValidationError(_(
                "No se encontraron líneas conciliables.\n"
                "Factura líneas: %s\n"
                "Pago líneas: %s"
            ) % (len(invoice_lines), len(payment_lines)))
            
        except Exception as e:
            _logger.error("Error conciliando factura %s con pago %s: %s", 
                         invoice.name, payment.name, str(e))
            raise ValidationError(_("Error al conciliar: %s") % str(e))
    
    def _create_historic_record(self, invoice, payment):
        self.ensure_one()
        
        if 'account.saving.payment' in self.env:
            try:
                historic_payment_vals = {
                    'saving_id': self.saving_id.id,
                    'payment_ref': payment.name,
                    'amount': self.payment_amount,
                    'payment_date': self.payment_date,
                    'payment_state': payment.state,
                    'type': 'payment',
                    'payment_journal_name': self.payment_journal_id.name,
                }
                self.env['account.saving.payment'].create(historic_payment_vals)
                _logger.info("Historic payment created successfully")
            except Exception as e:
                _logger.warning("Error creating historic payment: %s", str(e))
        
        if 'account.saving.invoice' in self.env:
            try:
                historic_invoice_vals = {
                    'saving_id': self.saving_id.id,
                    'invoice_ref': invoice.name,
                    'amount': invoice.amount_total,
                    'invoice_date': invoice.invoice_date,
                    'invoice_state': invoice.state,
                    'type': 'out_invoice',
                }
                self.env['account.saving.invoice'].create(historic_invoice_vals)
                _logger.info("Historic invoice created successfully")
            except Exception as e:
                _logger.warning("Error creating historic invoice: %s", str(e))
    
    def action_preview_invoice(self):
        self.ensure_one()
        
        if not self.saving_id:
            raise ValidationError(_("Debe seleccionar un plan de ahorro."))
        
        if not self.inscription_line_id:
            raise ValidationError(_("No se encontró una línea de inscripción en el plan."))
        
        try:
            invoice = self._create_inscription_invoice()
            invoice.button_draft()
            
            return {
                'type': 'ir.actions.act_window',
                'name': _('Previsualización Factura de Inscripción'),
                'res_model': 'account.move',
                'res_id': invoice.id,
                'view_mode': 'form',
                'target': 'new',
            }
        except Exception as e:
            raise ValidationError(_("Error al previsualizar: %s") % str(e))
    
    @api.model
    def default_get(self, fields_list):
        defaults = super(PaymentInscriptionWz, self).default_get(fields_list)
        
        active_id = self._context.get('active_id')
        if active_id and 'saving_id' in fields_list:
            saving = self.env['account.saving'].browse(active_id)
            if saving.exists():
                defaults['saving_id'] = saving.id
        
        return defaults