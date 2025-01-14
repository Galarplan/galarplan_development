from odoo import api, fields, models, _


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    tipo_cuenta = fields.Selection([
        ('Corriente', 'Cuenta Corriente'),
        ('Ahorro', 'Cuenta de Ahorros'),
        ('Tarjeta', 'Tarjeta de Credito'),
        ('Virtual', 'Virtual'),
        ], 'Tipo de Cuenta', default='Ahorro')
    

    # @api.model
    # def _get_supported_account_types(self):
    #     res = super()._get_supported_account_types()
    #     print('ressss==========',res)
    #     res.append(('bank', _('Normal')))
    #     return res