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

    # alex code
    def copy(self, default=None):
        default = dict(default or {})

        if self.vat:
            base_vat = self.vat
            new_vat = base_vat + '-COPIA'

            contador = 1

            while self.search_count([
                ('vat', '=', new_vat)
            ]):
                new_vat = f"{base_vat}-COPIA-{contador}"
                contador += 1

            default['vat'] = new_vat

        return super().copy(default)
    # fin alex code                

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
