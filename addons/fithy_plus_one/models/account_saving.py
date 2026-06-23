# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

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

    # --- Funciones de Facturación Automática (sin pagos) ---
    def first_payment(self):
        """
        Genera SOLO la factura para la primera parte de la inscripción (50%) + Cuota 1.
        NO crea el pago automáticamente.
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
        
        # Crear la factura para la cuota 1 con el monto parcial de inscripción
        invoice = self._create_invoice_for_quota(first_quota, first_inscription_amount)
        
        if not invoice:
            raise ValidationError(_("No se pudo generar la factura para la cuota 1."))

        # Mensaje de éxito
        self.message_post(
            body=f"✅ Factura 50+1 generada: {invoice.name} por ${invoice.amount_total:.2f}\n"
                 f"📄 Inscripción: ${first_inscription_amount:.2f}\n"
                 f"📄 Cuota 1: ${first_quota.principal_amount:.2f}",
            subject="Factura 50+1 - 1er Abono",
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
        Genera SOLO la factura para la segunda parte de la inscripción (50%) + Cuota 2.
        NO crea el pago automáticamente.
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
        
        # Verificar si ya se ha pagado la primera parte
        first_inscription_amount = inscription_line.serv_inscription_amount * (self.first_inscription_percentage / 100.0)
        
        # Calcular lo que falta por pagar de la inscripción
        remaining_inscription = inscription_line.serv_inscription_amount - total_paid_inscription
        
        # El monto a facturar es el menor entre lo que falta pagar y el monto de la segunda parte
        amount_to_invoice = min(remaining_inscription, second_inscription_amount)
        
        if amount_to_invoice <= 0:
            raise ValidationError(_("No hay saldo pendiente de inscripción para facturar."))

        # Crear la factura para la cuota 2 con el monto parcial de inscripción
        invoice = self._create_invoice_for_quota(second_quota, amount_to_invoice)
        
        if not invoice:
            raise ValidationError(_("No se pudo generar la factura para la cuota 2."))

        # Mensaje de éxito
        self.message_post(
            body=f"✅ Factura 50+1 generada: {invoice.name} por ${invoice.amount_total:.2f}\n"
                 f"📄 Inscripción: ${amount_to_invoice:.2f}\n"
                 f"📄 Cuota 2: ${second_quota.principal_amount:.2f}",
            subject="Factura 50+1 - 2do Abono",
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