from odoo import _, api, fields, models

class AccountMove(models.Model):
    _inherit = 'account.move'

    #   Tipo financiamiento
    financing_type = fields.Char(
        string='Tipo de Financiamiento',
        size=3
    )

    #   Valor financiamiento directo
    direct_financing_value = fields.Float(
        string='Valor Financiamiento Directo',
        digits=(16, 2)
    )

    #   Valor financiamiento externo
    external_financing_value = fields.Float(
        string='Valor Financiamiento Externo',
        digits=(16, 2)
    )
