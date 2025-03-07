from odoo import _, api, fields, models

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    bank_cheque_id = fields.Many2one('cheque.printing',string='Formato del cheque')

