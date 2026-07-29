from odoo import _, api, fields, models

class AccountSavingLines(models.Model):
    _inherit = 'account.saving.lines'


    discount = fields.Float('Discount')
    discount_value = fields.Float('Discount Value')
    last_serv_inscription_amount = fields.Float('Last inscription')
    last_date = fields.Date('Last Date')
    new_percent = fields.Float('New Percent')