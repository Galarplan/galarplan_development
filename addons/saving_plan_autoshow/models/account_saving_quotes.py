from odoo import _, api, fields, models

class AccountSavingQuotes(models.Model):
    _name = 'account.saving.quotes'

    saving_id = fields.Many2one('account.saving')

    number = fields.Integer('cuota')

    value = fields.Float('Valor')

    paid_value = fields.Float('Valor pagado')

    pending_value = fields.Float('Valor Pendiente')