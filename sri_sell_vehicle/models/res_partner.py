from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    country_substate_id = fields.Many2one(
        'res.country.substate',
        string='Subestado',
        help='Subestado relacionado con el país seleccionado.'
    )

    residence_type = fields.Selection(
        [
            ('RESIDENCIA', 'RESIDENCIA'),
            ('DEPARTAMENTO', 'DEPARTAMENTO'),
            ('OFICINA', 'OFICINA'),
            ('OTRO', 'OTRO'),
        ],
        string='Tipo de Residencia/Local',
        help='Tipo de residencia o local asociado al contacto.'
    )
    address_number = fields.Char(
        string='Número de Dirección', 
        help='Número de la dirección.'
    )
    intersection = fields.Char(
        string='Intersección', 
        help='Intersección cercana a la dirección.'
    )
