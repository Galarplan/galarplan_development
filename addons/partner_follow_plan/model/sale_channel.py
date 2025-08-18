from odoo import _, api, fields, models

class SaleChannelPlan(models.Model):
    _name = 'sale.channel.plan'
    _description = 'Canal de ventas galarplan'
    check_company = True

    company_id = fields.Many2one('res.company','Empresa')
    code = fields.Char('Codigo')
    name = fields.Char('Nombre')
