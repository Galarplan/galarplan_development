# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError,UserError

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    display_type = fields.Selection(
        selection=[
            ('product', 'Product'),
            ('cogs', 'Cost of Goods Sold'),
            ('tax', 'Tax'),
            ('rounding', "Rounding"),
            ('payment_term', 'Payment Term'),
            ('line_section', 'Section'),
            ('line_note', 'Note'),
            ('epd', 'Early Payment Discount'),
            ('planes', 'Planes de Ahorro')
        ],
        compute='_compute_display_type', store=True, readonly=False, precompute=True,
        required=True,
    )

    for_planes=fields.Boolean("Para planes de Ahorro",default=False)

    @api.depends('move_id')
    def _compute_display_type(self):
        for line in self.filtered(lambda l: not l.display_type):
            # avoid cyclic dependencies with _compute_account_id
            account_set = self.env.cache.contains(line, line._fields['account_id'])
            tax_set = self.env.cache.contains(line, line._fields['tax_line_id'])
            line.display_type = (
                'tax' if tax_set and line.tax_line_id else
                'payment_term'  if account_set and line.account_id.account_type in ['asset_receivable',
                                                                                   'liability_payable'] and not line.for_planes else
                'planes' if line.for_planes   else 'product'
            ) if line.move_id.is_invoice() else 'product'

    @api.constrains('account_id', 'display_type')
    def _check_payable_receivable(self):
        for line in self:
            account_type = line.account_id.account_type
            if line.move_id.is_sale_document(include_receipts=True):
                if not line.for_planes:
                    if account_type == 'liability_payable':
                        continue
                        raise UserError(
                            _("Account %s is of payable type, but is used in a sale operation.", line.account_id.code))
                    # if (line.display_type == 'payment_term') ^ (account_type == 'asset_receivable'):
                    #     raise UserError(_("Any journal item on a receivable account must have a due date and vice versa."))
            if line.move_id.is_purchase_document(include_receipts=True):
                if not line.for_planes:
                    if account_type == 'asset_receivable':
                        raise UserError(_("Account %s is of receivable type, but is used in a purchase operation.",
                                          line.account_id.code))
                    if (line.display_type == 'payment_term') ^ (account_type == 'liability_payable'):
                        raise UserError(_("Any journal item on a payable account must have a due date and vice versa."))
