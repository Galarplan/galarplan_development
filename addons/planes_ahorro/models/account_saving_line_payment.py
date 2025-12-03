# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError,UserError
import logging


_logger = logging.getLogger(__name__)




class AccountSavingLines(models.Model):
    _name = 'account.saving.line.payment'
    _description = 'listado de pagos para planes de ahorro'

    saving_id = fields.Many2one('account.saving', string='Plan de ahorro',ondelete="cascade"    )
    currency_id = fields.Many2one(related="saving_id.currency_id", string='Moneda', store=False, readonly=True)
    type=fields.Selection([('payment','Pago'),('historic','Historico')],default="payment",string="Tipo",required=True)
    number = fields.Integer(string='Número de cuota')
    date = fields.Date(string='Fecha de cuota')
    saving_line_id = fields.Many2one(
        'account.saving.lines', string="Linea de Ahorro")
    pendiente = fields.Monetary(string="H. Pendiente", digits=(16, 2))
    aplicado = fields.Float(string="Aplicado", digits=(16, 2))
    payment_id=fields.Many2one("account.payment","Pago")
    reconciled=fields.Boolean(string="Reconciliado",default=True)
    old_payment_id=fields.Many2one("account.saving.payment","Pago Migrado")

    old_ref_id = fields.Char("Antiguo REF ID", tracking=True)

    computed_payment_name = fields.Char(string="Nombre del Pago", compute="_compute_payment_name", store=True)

    @api.depends("payment_id", "old_payment_id")
    def _compute_payment_name(self):
        for record in self:
            record.computed_payment_name = record.payment_id.name if record.payment_id else record.old_payment_id.payment_ref

    @api.model
    def reconcile_invoice_with_payment(self, invoice_id, payment_id):
        """
        Conciliar una factura de venta con un cobro.

        :param invoice_id: ID de la factura (account.move)
        :param payment_id: ID del cobro (account.payment)
        :return: True si se realiza la conciliación correctamente, False en caso de error.
        """
        # try:
            # Obtener la factura y el pago
        invoice = self.env['account.move'].browse(invoice_id)
        payment = self.env['account.payment'].browse(payment_id)

        # Validaciones de existencia
        if not invoice.exists():
            raise UserError(_("La factura con ID %s no existe.") % invoice_id)
            
        if not payment.exists():
            raise UserError(_("El pago con ID %s no existe.") % payment_id)

        # Validar tipo de factura
        if invoice.move_type not in ('out_invoice', 'entry'):
            raise UserError(_("El ID proporcionado no corresponde a una factura de venta o asiento de ahorro."))

        # Validar tipo de pago
        if payment.payment_type != 'inbound':
            raise UserError(_("El ID proporcionado no corresponde a un cobro válido."))

        # Verificar estado de la factura
        if invoice.state != 'posted':
            raise UserError(_("La factura no está publicada. Estado actual: %s") % invoice.state)
            
        if not invoice.line_ids:
            raise UserError(_("La factura no tiene líneas contables."))

        # Verificar estado del pago
        if payment.state != 'posted':
            raise UserError(_("El cobro no está publicado. %s Estado actual: %s") % (payment.move_id.name,payment.state))
            
        if not payment.move_id:
            raise UserError(_("El cobro no tiene asiento contable asociado."))
            
        if not payment.move_id.line_ids:
            raise UserError(_("El cobro no tiene líneas contables."))

        # Obtener cuenta del partner
        partner_account = invoice.saving_id.property_account_receivable_id or invoice.partner_id.property_account_receivable_id
        
        if not partner_account:
            raise UserError(_("No se pudo determinar la cuenta por cobrar del partner."))

        # Obtener las líneas contables a conciliar
        invoice_lines = invoice.line_ids.filtered(
            lambda line: line.account_id.reconcile 
            and line.amount_residual != 0 
            and line.account_id == partner_account
        )

        payment_lines = payment.move_id.line_ids.filtered(
            lambda line: line.account_id.reconcile 
            and line.amount_residual != 0 
            and line.account_id == partner_account
        )

        
        # Si no hay líneas regulares, buscar líneas de prepago
        if not invoice_lines and not payment_lines:
            invoice_lines = invoice.line_ids.filtered(
                lambda line: line.account_id.reconcile 
                and line.account_id != partner_account 
                and line.account_id.prepayment_account
            )
            
            payment_lines = payment.move_id.line_ids.filtered(
                lambda line: line.account_id.reconcile 
                and line.account_id != partner_account 
                and line.account_id.prepayment_account
            )

            if not invoice_lines or not payment_lines:
                raise UserError(_("No se encontraron líneas contables para conciliar."))

            lines_to_reconcile = invoice_lines + payment_lines
            lines_to_reconcile.reconcile()
            return True

        # Manejo de prepagos si hay factura pero no líneas de pago regulares
        if invoice_lines and not payment_lines:
            payment_lines = payment.move_id.line_ids.filtered(
                lambda line: line.account_id.reconcile 
                and line.amount_residual != 0 
                and line.account_id != partner_account 
                and line.account_id.prepayment_account
            )
            
            if payment_lines:
                for prepayment_line in payment_lines:
                    reconcile_amount = min(abs(prepayment_line.amount_residual), abs(invoice.amount_residual))
                    
                    brw_assignment = self.env["account.prepayment.assignment"].create({
                        "move_id": invoice.id,
                        "prepayment_aml_id": prepayment_line.id,
                        "amount": reconcile_amount,
                        "date": fields.Date.context_today(self),
                        "company_id": invoice.company_id.id,
                        "new_journal_id": payment.journal_id.id
                    })
                    brw_assignment.button_confirm()
                return True

        # Validar que tenemos líneas para conciliar
        if not invoice_lines:
            raise UserError(_("No se encontraron líneas conciliables en la factura."))
            
        if not payment_lines:
            raise UserError(_("No se encontraron líneas conciliables en el pago."))

        # Realizar la conciliación regular
        lines_to_reconcile = invoice_lines + payment_lines
        lines_to_reconcile.reconcile()
        
        return True
            
        # except Exception as e:
        #     # Log del error para debugging
        #     _logger.error("Error conciliando factura %s con pago %s: %s", invoice_id, payment_id, str(e))
        #     raise ValidationError(_("Error conciliando factura y cobro: %s") % str(e))
