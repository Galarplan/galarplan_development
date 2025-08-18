from odoo import _, api, fields, models

class FeesEmployee(models.Model):
    _name = 'fees.employee'
    check_company=True

    company_id = fields.Many2one('res.company',default = lambda self: self.env.company.id)
    active = fields.Boolean('Activo')


