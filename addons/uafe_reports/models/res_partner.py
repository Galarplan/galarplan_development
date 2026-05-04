from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.constrains('vat')
    def _check_unique_vat(self):
        for record in self:
            if record.vat:
                existing = self.search([
                    ('vat', '=', record.vat),
                    ('id', '!=', record.id)
                ], limit=1)

                if existing:
                    raise ValidationError(
                        "Ya existe un cliente/proveedor con ese número de identificación."
                    )    

    economic_activity = fields.Many2one('economy.activity',string='Actividad Economica')
    monthly_income = fields.Float(string='Ingresos Mensuales')
    
#  Tipo de persona
    person_type = fields.Selection(
        [
            ('natural', 'Natural'),
            ('juridico', 'Jurídico')
        ],
        string='Tipo de Persona',
        default='natural')

# NUEVO --- PARA PARROQUIA ---
    parish_id = fields.Many2one(
        'res.country.parish',
        string='Parroquia')
