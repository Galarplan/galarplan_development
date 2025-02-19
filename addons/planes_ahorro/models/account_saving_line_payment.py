# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountSavingLines(models.Model):
    _name = 'account.saving.line.payment'
    _description = 'listado de pagos para planes de ahorro'

    saving_id = fields.Many2one('account.saving', string='Plan de ahorro',ondelete="cascade"    )
    currency_id = fields.Many2one(related="saving_id.currency_id", string='Moneda', store=False, readonly=True)
    number = fields.Integer(string='Número de cuota')
    date = fields.Date(string='Fecha de cuota')
    saving_line_id = fields.Many2one(
        'account.saving.lines', string="Linea de Ahorro")
    pendiente = fields.Monetary(string="H. Pendiente", digits=(16, 2))
    aplicado = fields.Float(string="Aplicado", digits=(16, 2))
    payment_id=fields.Many2one("account.payment","Pago")
    reconciled=fields.Boolean(string="Reconciliado",default=True)
    @api.model
    def reconcile_invoice_with_payment(self, invoice_id, payment_id):
        """
        Conciliar una factura de venta con un cobro.

        :param invoice_id: ID de la factura (account.move)
        :param payment_id: ID del cobro (account.payment)
        :return: True si se realiza la conciliación correctamente, False en caso de error.
        """
        try:
            # Obtener la factura y el pago
            invoice = self.env['account.move'].browse(invoice_id)
            payment = self.env['account.payment'].browse(payment_id)

            if not invoice or invoice.move_type != 'out_invoice':
                raise ValueError(_("El ID proporcionado no corresponde a una factura de venta."))

            if not payment or payment.payment_type != 'inbound':
                raise ValueError(_("El ID proporcionado no corresponde a un cobro válido."))

            # Verificar que ambos tengan asientos contables publicados
            if invoice.state != 'posted' or not invoice.line_ids:
                raise ValueError(_("La factura no está publicada o no tiene líneas contables."))

            if payment.state != 'posted' or not payment.move_id.line_ids:
                raise ValueError(_("El cobro no está publicado o no tiene líneas contables."))
            partner_account=invoice.partner_id.property_account_receivable_id
            # Obtener las líneas contables a conciliar
            invoice_lines = invoice.line_ids.filtered(
                lambda line: line.account_id.reconcile and line.amount_residual != 0 and line.account_id==partner_account)
            #print("factura",invoice_lines)
            payment_lines = payment.move_id.line_ids.filtered(
                lambda line: line.account_id.reconcile and line.account_id==partner_account)
            #print("pago", payment_lines)
            if not invoice_lines or not payment_lines:
                raise ValueError(_("No se encontraron líneas contables para conciliar."))

            # Realizar la conciliación
            lines_to_reconcile = invoice_lines + payment_lines
            lines_to_reconcile.reconcile()

            return True
        except Exception as e:
            raise ValidationError(_("Error conciliando factura y cobro: %s", str(e)))
