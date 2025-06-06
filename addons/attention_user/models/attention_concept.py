from odoo import models, fields, api, _

class AttentionConcept(models.Model):
    _name = 'attention.concept'
    _description = 'Conceptos de Atención'
    _order = 'name asc'
    
    code = fields.Char('Código', required=True)
    name = fields.Char('Nombre', required=True, translate=True)
    active = fields.Boolean('Activo', default=True)
    
    # Método name_get para mostrar mejor la información
    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.code}] {record.name}" if record.code else record.name
            result.append((record.id, name))
        return result
    
    # Método name_search para búsquedas más inteligentes
    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        if args is None:
            args = []
        domain = args + ['|', ('name', operator, name), ('code', operator, name)]
        return self._search(domain, limit=limit, access_rights_uid=name_get_uid)
    
    # Restricción para códigos únicos
    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'El código del concepto debe ser único!'),
    ]