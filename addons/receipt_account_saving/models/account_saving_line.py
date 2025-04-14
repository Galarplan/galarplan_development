from odoo import _, api, fields, models

class AccountSavingLine(models.Model):
    _inherit = 'account.saving.lines'


    deposit_date = fields.Date('Deposito Cliente')

    def print_receipt(self):
        self.ensure_one()
        return self.env.ref('receipt_account_saving.action_receipt_saving_line').report_action(self)
