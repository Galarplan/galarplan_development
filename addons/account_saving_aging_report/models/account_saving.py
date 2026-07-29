from odoo import _, api, fields, models

class AccountSaving(models.Model):
    _inherit = 'account.saving'

    vehicle_invoice_id = fields.Many2one('account.move')

    legal_invoice_id = fields.Many2one('account.move')

    device_invoice_id = fields.Many2one('account.move')

    adjudicate_date = fields.Date('Fecha adj')

    official_id = fields.Many2one('res.partner')