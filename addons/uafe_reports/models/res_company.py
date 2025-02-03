from odoo import models, fields


class ResCompany(models.Model):
    
    _inherit = 'res.company'

    uafe_code = fields.Char(string='Codigo Uafe')
