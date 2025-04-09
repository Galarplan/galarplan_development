from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
import math


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    is_roundoff_line = fields.Boolean('Roundoff Line', default=False)



class AccountMove(models.Model):
    _inherit = 'account.move'

    # round_off_value = fields.Monetary(string='Round off amount', compute='_compute_amount', store=True, readonly=True)
    round_off_value = fields.Monetary(string='Round off amount',readonly=True)
    round_off_amount = fields.Float(string='Round off Amount')  # Manual override si aplica
    # rounded_total = fields.Monetary(string='Rounded Total', compute='_compute_amount', store=True, readonly=True)
    rounded_total = fields.Monetary(string='Rounded Total',readonly=True)
    round_active = fields.Boolean(
        string='Enabled Roundoff',
        default=lambda self: self.env['ir.config_parameter'].sudo().get_param('account.invoice_roundoff')
    )

    # @api.depends(
    #     'invoice_line_ids.amount_currency',
    #     'invoice_line_ids.amount_residual',
    #     'invoice_line_ids.tax_ids',
    #     'line_ids.debit', 'line_ids.credit',
    #     'line_ids.balance', 'line_ids.amount_currency',
    #     'line_ids.account_id',
    # )
    # def _compute_amount(self):
    #     currencies = {}
    #     for move in self:
    #         if not move.is_invoice(include_receipts=True):
    #             continue

    #         # Valores base
    #         total_untaxed = total_tax = total = 0.0
    #         total_currency = total_residual = total_residual_currency = 0.0
    #         round_off = 0.0

    #         move_currencies = set()
    #         for line in move.line_ids:
    #             if line.is_roundoff_line:
    #                 continue

    #             if line.currency_id:
    #                 move_currencies.add(line.currency_id)

    #             if not line.display_type:
    #                 total_untaxed += line.balance
    #                 total += line.balance
    #                 total_currency += line.amount_currency
    #             elif line.tax_line_id:
    #                 total_tax += line.balance
    #                 total += line.balance
    #                 total_currency += line.amount_currency
    #             elif line.account_id.account_type in ('asset_receivable', 'liability_payable'):
    #                 total_residual += line.amount_residual
    #                 total_residual_currency += line.amount_residual_currency

    #         one_currency = len(move_currencies) == 1
    #         currency = move_currencies.pop() if one_currency else move.company_id.currency_id
    #         sign = move.move_type in ['out_invoice', 'in_receipt', 'out_receipt'] and 1 or -1

    #         move.amount_untaxed = sign * (total_untaxed if not one_currency else total_currency)
    #         move.amount_tax = sign * (total_tax if not one_currency else total_currency)
    #         move.amount_total = sign * (total if not one_currency else total_currency)
    #         move.amount_residual = -sign * (total_residual if not one_currency else total_residual_currency)
    #         move.amount_untaxed_signed = -total_untaxed
    #         move.amount_tax_signed = -total_tax
    #         move.amount_total_signed = abs(total) if move.move_type == 'entry' else -total
    #         move.amount_residual_signed = total_residual

    #         # Roundoff solo si está activo
    #         if move.round_active and move.amount_tax:
    #             total_sales = 0.0
    #             total_other = 0.0

    #             for line in move.invoice_line_ids:
    #                 for tax in line.tax_ids:
    #                     factor = tax.amount * line.price_subtotal / 100.0
    #                     if tax.other_tax:
    #                         total_other += factor
    #                     else:
    #                         total_sales += factor

    #             def custom_round(val):
    #                 mod = val % 1
    #                 if mod >= 0.5:
    #                     return math.ceil(val)
    #                 elif 0 < mod < 0.5:
    #                     return round(val) + 0.5
    #                 return val

    #             total_rounded = custom_round(total_sales) + custom_round(total_other)
    #             round_off = total_rounded - move.amount_tax

    #             move.round_off_value = round_off
    #             move.round_off_amount = round_off
    #             move.rounded_total = move.amount_untaxed + total_rounded
    #             move.amount_total = move.amount_untaxed + total_rounded

    # def _construct_values(self, account_id, amount):
    #     return [0, 0, {
    #         'name': _('Roundoff Amount'),
    #         'account_id': account_id,
    #         'quantity': 1,
    #         'price_unit': amount,
    #         'is_roundoff_line': True,
    #         'is_rounding_line': False,
    #     }]

    # @api.model_create_multi
    # def create(self, vals_list):
    #     for vals in vals_list:
    #         if vals.get('round_active') and vals.get('round_off_amount'):
    #             account_id = int(self.env['ir.config_parameter'].sudo().get_param("account.roundoff_account_id") or 0)
    #             if account_id:
    #                 values = self._construct_values(account_id, vals['round_off_amount'])
    #                 vals.setdefault('invoice_line_ids', []).append(values)
    #                 vals.setdefault('line_ids', []).append(values)
    #     return super().create(vals_list)


class AccountTax(models.Model):
    _inherit = 'account.tax'

    other_tax = fields.Boolean("Other Tax", default = False)