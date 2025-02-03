from odoo import models, fields, api


class ResCountry(models.Model):
    _inherit = 'res.country'
    

    nationality_code= fields.Char(string='Codigo Nacionalidad')