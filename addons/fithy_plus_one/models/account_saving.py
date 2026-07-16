# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class AccountSaving(models.Model):
    _inherit = 'account.saving'

    # --- Campos para Pagos Automáticos ---
    enable_automatic_payments = fields.Boolean(
        string='Habilitar 50+1',
        default=False,
        help="Activa esta opción para habilitar los pagos automáticos"
    )
    
    first_inscription_percentage = fields.Float(
        string='% 1er Pago Inscripción',
        default=50.0,
        help="Porcentaje del valor de inscripción para el primer pago",
        digits=(16, 2)
    )
    
    second_inscription_percentage = fields.Float(
        string='% 2do Pago Inscripción',
        default=50.0,
        help="Porcentaje del valor de inscripción para el segundo pago",
        digits=(16, 2)
    )

    # Campos calculados para mostrar montos
    first_inscription_amount = fields.Float(
        string='Valor 1er Pago',
        compute='_compute_inscription_amounts',
        digits=(16, 2)
    )
    
    second_inscription_amount = fields.Float(
        string='Valor 2do Pago',
        compute='_compute_inscription_amounts',
        digits=(16, 2)
    )

    # Campos para estado de pagos
    first_payment_status = fields.Selection([
        ('no_aplicable', 'No Aplicable'),
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado')
    ], string='1er Pago', compute='_compute_payment_status', store=True)
    
    second_payment_status = fields.Selection([
        ('no_aplicable', 'No Aplicable'),
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado')
    ], string='2do Pago', compute='_compute_payment_status', store=True)

    first_payment_date = fields.Date(
        string='Fecha 1er Pago', 
        compute='_compute_payment_dates',
        store=True
    )
    second_payment_date = fields.Date(
        string='Fecha 2do Pago', 
        compute='_compute_payment_dates',
        store=True
    )
    
    first_invoice_id = fields.Many2one(
        'account.move', 
        string='Factura 1er Pago', 
        compute='_compute_payment_invoices'
    )
    second_invoice_id = fields.Many2one(
        'account.move', 
        string='Factura 2do Pago', 
        compute='_compute_payment_invoices'
    )

    first_payment_info = fields.Text(
        string='Info 1er Pago', 
        compute='_compute_payment_info'
    )
    second_payment_info = fields.Text(
        string='Info 2do Pago', 
        compute='_compute_payment_info'
    )

    # --- Métodos de Cómputo Optimizados ---
    @api.depends('enable_automatic_payments', 'serv_inscription_amount', 
                 'first_inscription_percentage', 'second_inscription_percentage')
    def _compute_inscription_amounts(self):
        """Solo calcula si enable_automatic_payments está activado"""
        for record in self:
            if record.enable_automatic_payments:
                record.first_inscription_amount = record.serv_inscription_amount * (record.first_inscription_percentage / 100.0)
                record.second_inscription_amount = record.serv_inscription_amount * (record.second_inscription_percentage / 100.0)
            else:
                record.first_inscription_amount = 0.0
                record.second_inscription_amount = 0.0

    @api.depends('enable_automatic_payments', 'line_ids', 'line_ids.estado_pago')
    def _compute_payment_status(self):
        """Solo calcula si enable_automatic_payments está activado"""
        for record in self:
            if record.enable_automatic_payments:
                # Verificar cuota 1
                first_quota = record.line_ids.filtered(lambda l: l.number == 1)
                if first_quota:
                    if first_quota.estado_pago == 'pagado':
                        record.first_payment_status = 'pagado'
                    else:
                        record.first_payment_status = 'pendiente'
                else:
                    record.first_payment_status = 'no_aplicable'

                # Verificar cuota 2
                second_quota = record.line_ids.filtered(lambda l: l.number == 2)
                if second_quota:
                    if second_quota.estado_pago == 'pagado':
                        record.second_payment_status = 'pagado'
                    else:
                        record.second_payment_status = 'pendiente'
                else:
                    record.second_payment_status = 'no_aplicable'
            else:
                record.first_payment_status = 'no_aplicable'
                record.second_payment_status = 'no_aplicable'

    @api.depends('enable_automatic_payments', 'line_ids', 'line_ids.payment_ids', 'line_ids.payment_ids.date')
    def _compute_payment_dates(self):
        """Solo calcula si enable_automatic_payments está activado"""
        for record in self:
            if record.enable_automatic_payments:
                # Fecha del primer pago (cuota 1)
                first_quota = record.line_ids.filtered(lambda l: l.number == 1)
                if first_quota and first_quota.payment_ids:
                    payment = first_quota.payment_ids.filtered(lambda p: p.state == 'posted')
                    record.first_payment_date = payment[0].date if payment else False
                else:
                    record.first_payment_date = False

                # Fecha del segundo pago (cuota 2)
                second_quota = record.line_ids.filtered(lambda l: l.number == 2)
                if second_quota and second_quota.payment_ids:
                    payment = second_quota.payment_ids.filtered(lambda p: p.state == 'posted')
                    record.second_payment_date = payment[0].date if payment else False
                else:
                    record.second_payment_date = False
            else:
                record.first_payment_date = False
                record.second_payment_date = False

    @api.depends('enable_automatic_payments', 'line_ids', 'line_ids.invoice_id')
    def _compute_payment_invoices(self):
        """Solo calcula si enable_automatic_payments está activado"""
        for record in self:
            if record.enable_automatic_payments:
                first_quota = record.line_ids.filtered(lambda l: l.number == 1)
                record.first_invoice_id = first_quota.invoice_id.id if first_quota and first_quota.invoice_id else False

                second_quota = record.line_ids.filtered(lambda l: l.number == 2)
                record.second_invoice_id = second_quota.invoice_id.id if second_quota and second_quota.invoice_id else False
            else:
                record.first_invoice_id = False
                record.second_invoice_id = False

    @api.depends('enable_automatic_payments', 'first_payment_status', 'second_payment_status', 
                 'first_inscription_amount', 'second_inscription_amount')
    def _compute_payment_info(self):
        """Solo calcula si enable_automatic_payments está activado"""
        for record in self:
            if record.enable_automatic_payments:
                record.first_payment_info = f"Estado: {dict(record._fields['first_payment_status'].selection).get(record.first_payment_status)}\nMonto: {record.first_inscription_amount:.2f}"
                record.second_payment_info = f"Estado: {dict(record._fields['second_payment_status'].selection).get(record.second_payment_status)}\nMonto: {record.second_inscription_amount:.2f}"
            else:
                record.first_payment_info = "Modalidad 50+1 no habilitada"
                record.second_payment_info = "Modalidad 50+1 no habilitada"

    def _create_invoice_for_quota(self, quota_line, inscription_amount):
        """
        Crea una factura para una cuota específica con el monto de inscripción parcial.
        
        :param quota_line: Línea de la cuota (account.saving.lines)
        :param inscription_amount: Monto de inscripción a facturar
        :return: La factura creada (account.move)
        """
        # Guardar el valor original de la inscripción
        original_inscription_amount = quota_line.serv_inscription_amount
        
        try:
            # Asignar el monto parcial de inscripción a la cuota
            quota_line.serv_inscription_amount = inscription_amount
            
            # Habilitar la cuota para facturar
            quota_line.enabled_for_invoice = True
            
            # Generar la factura con contexto para publicar automáticamente
            quota_line.with_context(post=True).action_invoice()
            
        finally:
            # Restaurar el valor original de la inscripción
            quota_line.serv_inscription_amount = original_inscription_amount
            # Deshabilitar la cuota para facturación manual
            quota_line.enabled_for_invoice = False
        
        return quota_line.invoice_id

    def _create_payment_for_invoice(self, invoice, quota_line, total_amount):
        """
        Crea un pago para una factura específica y lo concilia.
        SOLO PARA EL VALOR DE LA CUOTA (saving_amount)
        """
        self.ensure_one()
        
        # Buscar un diario de pago
        payment_journal = self.env['account.journal'].search([
            ('type', 'in', ['bank', 'cash']),
            ('company_id', '=', self.company_id.id)
        ], limit=1)
        
        if not payment_journal:
            raise ValidationError(_("No se encontró un diario de pago válido."))
        
        # Obtener método de pago
        payment_method = payment_journal.inbound_payment_method_line_ids[:1].payment_method_id
        
        # Crear el pago - USAR SOLO EL saving_amount (sin inscripción)
        payment_vals = {
            'date': fields.Date.context_today(self),
            'journal_id': payment_journal.id,
            'payment_method_id': payment_method.id if payment_method else False,
            'company_id': self.company_id.id,
            'amount': quota_line.saving_amount,  # SOLO EL VALOR DE LA CUOTA
            'currency_id': self.currency_id.id,
            'partner_type': 'customer',
            'partner_id': self.partner_id.id,
            'ref': f"50+1 - {self.name} - Cuota {quota_line.number}",
            'state': 'draft',
            'saving_line_id': quota_line.id,
            'saving_id': self.id,
        }
        
        payment = self.env['account.payment'].create(payment_vals)
        
        # Publicar el pago
        payment.action_post()
        
        # Conciliar la factura con el pago
        try:
            self.env['account.saving.line.payment'].reconcile_invoice_with_payment(invoice.id, payment.id)
            _logger.info("✅ Factura %s conciliada con pago %s", invoice.name, payment.name)
        except Exception as e:
            _logger.warning("No se pudo conciliar automáticamente: %s", str(e))
        
        # --- CREAR REGISTRO EN account.saving.line.payment CON SQL ---
        query_payment_line = """
            INSERT INTO account_saving_line_payment (
                saving_id, 
                saving_line_id, 
                number, 
                date, 
                payment_id, 
                aplicado, 
                pendiente, 
                type, 
                reconciled,
                create_date,
                write_date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        self.env.cr.execute(query_payment_line, (
            self.id,                        # saving_id
            quota_line.id,                  # saving_line_id
            quota_line.number,              # number
            fields.Date.context_today(self), # date
            payment.id,                     # payment_id
            quota_line.saving_amount,       # aplicado (SOLO el valor de la cuota)
            0.0,                            # pendiente
            'payment',                      # type
            True                            # reconciled
        ))
        
        _logger.info("✅ Registro en account.saving.line.payment creado para cuota %s con monto %s", 
                    quota_line.number, quota_line.saving_amount)
        
        return payment

    def _create_invoice_and_payment_for_quota(self, quota_line, inscription_amount):
        """
        Crea una factura para una cuota específica con el monto de inscripción parcial,
        Y CREA EL PAGO AUTOMÁTICAMENTE.
        El pago será SOLO por el valor de la cuota (saving_amount)
        """
        self.ensure_one()
        
        # Crear la factura
        invoice = self._create_invoice_for_quota(quota_line, inscription_amount)
        
        if not invoice:
            raise ValidationError(_("No se pudo generar la factura."))
        
        # --- CREAR EL PAGO - SOLO POR EL saving_amount ---
        payment = self._create_payment_for_invoice(invoice, quota_line, quota_line.saving_amount)
        
        # --- ACTUALIZAR CUOTA CERO (INSCRIPCIÓN) CON SQL ---
        inscription_line = self.line_ids.filtered(lambda l: l.number == 0)
        if inscription_line:
            # Calcular nuevo pagado
            nuevo_pagado = inscription_line.pagos or 0.0
            nuevo_pagado += inscription_amount
            nuevo_pendiente = inscription_line.serv_inscription_amount - nuevo_pagado
            
            if nuevo_pendiente < 0:
                nuevo_pendiente = 0.0
            
            estado_pago = 'pagado' if nuevo_pendiente <= 0.01 else 'pendiente'
            remanente = 0.0 if nuevo_pendiente <= 0.01 else nuevo_pendiente
            
            # Actualizar cuota cero con SQL
            query_inscription = """
                UPDATE account_saving_lines 
                SET 
                    pagos = %s,
                    pendiente = %s,
                    estado_pago = %s,
                    remanente = %s
                WHERE id = %s
            """
            self.env.cr.execute(query_inscription, (nuevo_pagado, nuevo_pendiente, estado_pago, remanente, inscription_line.id))
            
            _logger.info("✅ Cuota cero actualizada: pagos=%s, pendiente=%s", nuevo_pagado, nuevo_pendiente)
        
        # --- ACTUALIZAR LA CUOTA FACTURADA CON SQL ---
        # La cuota se marca como pagada con el valor de saving_amount
        query_quota = """
            UPDATE account_saving_lines 
            SET 
                pagos = %s,
                pendiente = %s,
                estado_pago = %s,
                remanente = %s
            WHERE id = %s
        """
        self.env.cr.execute(query_quota, (quota_line.saving_amount, 0.0, 'pagado', 0.0, quota_line.id))
        
        _logger.info("✅ Cuota %s actualizada: pagos=%s, pendiente=%s", 
                    quota_line.number, quota_line.saving_amount, 0.0)
        
        # --- REGISTRAR EL PAGO EN LA LÍNEA DE LA CUOTA (payment_ids) ---
        quota_line.write({
            'payment_ids': [(4, payment.id)]
        })
        
        _logger.info("✅ Pago %s vinculado a cuota %s con monto %s", 
                    payment.id, quota_line.id, quota_line.saving_amount)
        
        return invoice, payment

    # --- Funciones de Facturación Automática CON PAGO ---
    def first_payment(self):
        """
        Genera la factura y EL PAGO para la primera parte de la inscripción (50%) + Cuota 1.
        El pago será SOLO por el valor de la cuota 1 (saving_amount)
        """
        self.ensure_one()
        
        if self.state != 'open':
            raise ValidationError(_("El plan debe estar en estado 'Abierto' para procesar el primer pago."))
        
        if not self.enable_automatic_payments:
            raise ValidationError(_("La opción 'Habilitar 50+1' no está activada."))

        # Obtener líneas
        inscription_line = self.line_ids.filtered(lambda l: l.number == 0)
        first_quota = self.line_ids.filtered(lambda l: l.number == 1)
        
        if not inscription_line:
            raise ValidationError(_("No se encontró la línea de inscripción (cuota 0)."))
        if not first_quota:
            raise ValidationError(_("No se encontró la cuota número 1."))
        if first_quota.invoice_id:
            raise ValidationError(_("La cuota 1 ya tiene una factura asociada."))

        # Calcular el monto de la primera parte de la inscripción
        first_inscription_amount = inscription_line.serv_inscription_amount * (self.first_inscription_percentage / 100.0)
        
        # Crear la factura y el pago
        invoice, payment = self._create_invoice_and_payment_for_quota(first_quota, first_inscription_amount)

        # Mensaje de éxito
        self.message_post(
            body=f"✅ Factura y Pago 50+1 generados:\n"
                 f"📄 Factura: {invoice.name} por ${invoice.amount_total:.2f}\n"
                 f"💳 Pago: {payment.name} por ${payment.amount:.2f}\n"
                 f"📄 Inscripción: ${first_inscription_amount:.2f}\n"
                 f"📄 Cuota 1: ${first_quota.saving_amount:.2f}\n"
                 f"📌 Total factura: ${invoice.amount_total:.2f}",
            subject="Pago 50+1 - 1er Abono",
            message_type="notification",
            subtype_xmlid="mail.mt_note"
        )

        # Abrir la factura creada
        return {
            'type': 'ir.actions.act_window',
            'name': _('Factura Creada'),
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': invoice.id,
            'target': 'current',
        }

    def second_payment(self):
        """
        Genera la factura y EL PAGO para la segunda parte de la inscripción (50%) + Cuota 2.
        El pago será SOLO por el valor de la cuota 2 (saving_amount)
        """
        self.ensure_one()
        
        if self.state != 'open':
            raise ValidationError(_("El plan debe estar en estado 'Abierto' para procesar el segundo pago."))
        
        if not self.enable_automatic_payments:
            raise ValidationError(_("La opción 'Habilitar 50+1' no está activada."))

        # Obtener líneas
        inscription_line = self.line_ids.filtered(lambda l: l.number == 0)
        second_quota = self.line_ids.filtered(lambda l: l.number == 2)
        
        if not inscription_line:
            raise ValidationError(_("No se encontró la línea de inscripción (cuota 0)."))
        if not second_quota:
            raise ValidationError(_("No se encontró la cuota número 2."))
        if second_quota.invoice_id:
            raise ValidationError(_("La cuota 2 ya tiene una factura asociada."))

        # Verificar si ya se ha pagado parte de la inscripción
        existing_payments = self.env['account.saving.line.payment'].search([
            ('saving_line_id', '=', inscription_line.id),
            ('payment_id', '!=', False)
        ])
        total_paid_inscription = sum(existing_payments.mapped('aplicado'))
        
        # Calcular el monto de la segunda parte de la inscripción
        second_inscription_amount = inscription_line.serv_inscription_amount * (self.second_inscription_percentage / 100.0)
        
        # Calcular lo que falta por pagar de la inscripción
        remaining_inscription = inscription_line.serv_inscription_amount - total_paid_inscription
        
        # El monto a facturar es el menor entre lo que falta pagar y el monto de la segunda parte
        amount_to_invoice = min(remaining_inscription, second_inscription_amount)
        
        if amount_to_invoice <= 0:
            raise ValidationError(_("No hay saldo pendiente de inscripción para facturar."))

        # Crear la factura y el pago
        invoice, payment = self._create_invoice_and_payment_for_quota(second_quota, amount_to_invoice)

        # Mensaje de éxito
        self.message_post(
            body=f"✅ Factura y Pago 50+1 generados:\n"
                 f"📄 Factura: {invoice.name} por ${invoice.amount_total:.2f}\n"
                 f"💳 Pago: {payment.name} por ${payment.amount:.2f}\n"
                 f"📄 Inscripción: ${amount_to_invoice:.2f}\n"
                 f"📄 Cuota 2: ${second_quota.saving_amount:.2f}\n"
                 f"📌 Total factura: ${invoice.amount_total:.2f}",
            subject="Pago 50+1 - 2do Abono",
            message_type="notification",
            subtype_xmlid="mail.mt_note"
        )

        # Abrir la factura creada
        return {
            'type': 'ir.actions.act_window',
            'name': _('Factura Creada'),
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': invoice.id,
            'target': 'current',
        }