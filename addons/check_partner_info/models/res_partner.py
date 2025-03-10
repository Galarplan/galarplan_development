from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    cliente_proveedor_verificado = fields.Boolean(string='Cliente/Proveedor Verificado', default=False)