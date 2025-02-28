from odoo import _, api, fields, models

class AccountMove(models.Model):
    _inherit = 'account.move'


    manual_date = fields.Date(string='Manual Date')
    manual_document_number = fields.Char(string="Manual Document Number")