from odoo import models, fields

class VehicleType(models.Model):
    _inherit = 'vehicle.type'

    uafe_code = fields.Char(string='Código UAFE')