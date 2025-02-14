from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime


class AccountPaymentMethod(models.TransientModel):
    _inherit = "account.payment.register"

    show_mature_date = fields.Boolean(
    compute='_compute_mature_date_visibility',
    string="Show Mature Date",
    help="Indica si el campo 'mature_date' debe mostrarse y ser requerido.")

    mature_date = fields.Date('Fecha del Cheque/Mature Date')
    bank_id = fields.Many2one('res.bank', string='Banco')
    cheque_no = fields.Char('Cheque No')



    @api.depends('payment_method_code')
    def _compute_mature_date_visibility(self):
        """
        Computa si el campo 'mature_date' debe mostrarse y ser requerido.
        - Se muestra si el método de pago es 'pdc'.
        - Es requerido si el método de pago es 'pdc' y el estado no es 'posted'.
        """
        for payment in self:
            if payment.payment_method_code == 'pdc':
                payment.show_mature_date = True
            else:
                payment.show_mature_date = False
    

    def _create_payment_vals_from_wizard(self, batch_result):
        payment_vals = {
            'date': self.payment_date,
            'mature_date': self.mature_date,
            'bank_id': self.bank_id.id,
            'cheque_no':self.cheque_no,
            'amount': self.amount,
            'payment_type': self.payment_type,
            'partner_type': self.partner_type,
            'ref': self.communication,
            'journal_id': self.journal_id.id,
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'partner_bank_id': self.partner_bank_id.id,
            'payment_method_line_id': self.payment_method_line_id.id,
            'destination_account_id': self.line_ids[0].account_id.id,
            'write_off_line_vals': [],
        }

        conversion_rate = self.env['res.currency']._get_conversion_rate(
            self.currency_id,
            self.company_id.currency_id,
            self.company_id,
            self.payment_date,
        )

        if self.payment_difference_handling == 'reconcile':

            if self.early_payment_discount_mode:
                epd_aml_values_list = []
                for aml in batch_result['lines']:
                    if aml._is_eligible_for_early_payment_discount(self.currency_id, self.payment_date):
                        epd_aml_values_list.append({
                            'aml': aml,
                            'amount_currency': -aml.amount_residual_currency,
                            'balance': aml.company_currency_id.round(-aml.amount_residual_currency * conversion_rate),
                        })

                open_amount_currency = self.payment_difference * (-1 if self.payment_type == 'outbound' else 1)
                open_balance = self.company_id.currency_id.round(open_amount_currency * conversion_rate)
                early_payment_values = self.env['account.move']._get_invoice_counterpart_amls_for_early_payment_discount(epd_aml_values_list, open_balance)
                for aml_values_list in early_payment_values.values():
                    payment_vals['write_off_line_vals'] += aml_values_list

            elif not self.currency_id.is_zero(self.payment_difference):
                if self.payment_type == 'inbound':
                    # Receive money.
                    write_off_amount_currency = self.payment_difference
                else: # if self.payment_type == 'outbound':
                    # Send money.
                    write_off_amount_currency = -self.payment_difference

                write_off_balance = self.company_id.currency_id.round(write_off_amount_currency * conversion_rate)
                payment_vals['write_off_line_vals'].append({
                    'name': self.writeoff_label,
                    'account_id': self.writeoff_account_id.id,
                    'partner_id': self.partner_id.id,
                    'currency_id': self.currency_id.id,
                    'amount_currency': write_off_amount_currency,
                    'balance': write_off_balance,
                })
        return payment_vals

                