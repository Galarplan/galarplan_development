# Copyright (C) Softhealer Technologies.

from odoo import models, fields, api, _
from odoo.exceptions import UserError

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
}

# Since invoice amounts are unsigned, this is how we know if money comes in or goes out
MAP_INVOICE_TYPE_PAYMENT_SIGN = {
    'out_invoice': 1,
    'in_refund': -1,
    'in_invoice': -1,
    'out_refund': 1,
}


class sh_mip_register_payment_wizard(models.TransientModel):
    _name = "sh.mip.register.payment.wizard"
    _description = "Register Payment Wizard For Multi Invoice Payment"

    journal_id = fields.Many2one('account.journal', string='Payment Journal', required=True, domain=[
                                 ('type', 'in', ('bank', 'cash'))])
    payment_date = fields.Date(
        string='Payment Date', default=fields.Date.context_today, required=True, copy=False)
    communication = fields.Char(string='Memo')
    register_payment_line = fields.One2many(
        "sh.mip.register.payment.line", "wizard_id", string="Register Payment Line")

    def action_validate_multi_invoice_payment(self):
        if self and self.register_payment_line and self.journal_id:
            account_payment_obj = self.env['account.payment']
            payment_ids = []
            for payment_line in self.register_payment_line:
                if payment_line.invoice_id:
                    payment_type = False
                    if payment_line.invoice_id.move_type == 'out_invoice':
                        payment_type = 'inbound'
                    elif payment_line.invoice_id.move_type == 'out_refund':
                        payment_type = 'outbound'
                    elif payment_line.invoice_id.move_type == 'in_invoice':
                        payment_type = 'outbound'
                    elif payment_line.invoice_id.move_type == 'in_refund':
                        payment_type = 'inbound'
                    amount = payment_line.invoice_id.amount_residual * \
                        MAP_INVOICE_TYPE_PAYMENT_SIGN[payment_line.invoice_id.move_type]
#
                    payment_methods = payment_type == 'inbound' and self.journal_id.available_payment_method_ids 
                    payment_method_id = payment_methods and payment_methods[0] or False

                    payment_vals2 = {
                        'journal_id': self.journal_id.id,
                        'payment_method_id': payment_method_id.id if payment_method_id else '',
                        'date': self.payment_date,
                        'ref': self.communication,
                        'payment_type': payment_type,
                        'amount': payment_line.payment_amount,
                        'currency_id': payment_line.invoice_id.currency_id.id,
                        'partner_id': payment_line.invoice_id.commercial_partner_id.id,
                        'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[payment_line.invoice_id.move_type],
                    }

                    created_payment = account_payment_obj.create(payment_vals2)
                    if created_payment:
                        created_payment.action_post()

                        # reconcile with invoice
                        if created_payment.move_id:

                            if created_payment.move_id.line_ids.filtered(lambda x: x.account_id.account_type in ('asset_receivable', 'liability_payable')):
                                lines = created_payment.move_id.line_ids.filtered(
                                    lambda x: x.account_id.account_type in ('asset_receivable', 'liability_payable'))
                                lines += payment_line.invoice_id.line_ids.filtered(
                                    lambda line: line.account_id == lines[0].account_id and not line.reconciled)
                                lines.reconcile()

                        payment_ids.append(created_payment.id)

            if payment_ids:
                return {
                    'name': _('Payments'),
                    'domain': [('id', 'in', payment_ids), ('state', '=', 'posted')],
                    'view_mode': 'tree,form',
                    'res_model': 'account.payment',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                }

    @api.model
    def default_get(self,  default_fields):
        res = super(sh_mip_register_payment_wizard,
                    self).default_get(default_fields)
        active_ids = self._context.get('active_ids')
        # Check for selected invoices ids
        if not active_ids:
            raise UserError(
                _("Programming error: wizard action executed without active_ids in context."))

        invoices = self.env['account.move'].browse(active_ids)

        # Check all invoices are open
        if invoices:
            for invoice in invoices:
                if invoice.state != 'posted' and invoice.state == 'draft':
                    invoice.action_post()
        if any(invoice.state != 'posted' for invoice in invoices):
            raise UserError(
                _("You can only register payments for draft or open invoices"))
        # Check all invoices have the same currency
        if any(inv.currency_id != invoices[0].currency_id for inv in invoices):
            raise UserError(
                _("In order to pay multiple invoices at once, they must use the same currency."))

        if invoices:
            payment_line_list = []
            for inv in invoices:
                payment_line_vals = {}
                payment_line_vals = {
                    'invoice_id': inv.id,
                    'currency_id': inv.currency_id.id if inv.currency_id else False,
                    'partner_id': inv.partner_id.id if inv.partner_id else False,
                    'amount_total': inv.amount_total,
                    'residual': inv.amount_residual,
                    'payment_amount': inv.amount_residual
                }

                payment_line_list.append((0, 0, payment_line_vals))

        res.update({
            'register_payment_line': payment_line_list
        })
        return res


class sh_mip_register_payment_line(models.TransientModel):
    _name = "sh.mip.register.payment.line"
    _description = "Register Payment line For Multi Invoice Payment"

    wizard_id = fields.Many2one(
        "sh.mip.register.payment.wizard", string="Wizard")
    invoice_id = fields.Many2one("account.move", string="Invoice")
    currency_id = fields.Many2one('res.currency', string='Currency')
    partner_id = fields.Many2one("res.partner", string="Partner")
    amount_total = fields.Monetary(string='Total')
    residual = fields.Monetary(string='Amount Due')

    @api.model
    def _get_default_amount(self):
        return self.residual or 0.0

    payment_amount = fields.Monetary(
        string='Payment Amount', required=True, currency_field='currency_id', default=_get_default_amount)
