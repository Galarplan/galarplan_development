from odoo import _, api, fields, models

class LocationPlaces(models.Model):
    _name = 'location.places'
    _description = 'Localizaciones'
    check_company = True

    company_id = fields.Many2one('res.company','Empresa')
    code = fields.Char('Codigo')
    name = fields.Char('Nombre')