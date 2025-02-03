from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    economic_activity = fields.Many2one('economy.activity',string='Actividad Economica')
    monthly_income = fields.Float(string='Ingresos Mensuales')
    
