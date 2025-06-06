from odoo import models, fields, api, _

class DocumentAction(models.Model):
    _name = 'document.action'
    _description = 'Acciones de Documentos'
    _order = 'sequence, name asc'
    
    code = fields.Char(
        string='Código', 
        required=True,
        help="Código único para identificar la acción"
    )
    name = fields.Char(
        string='Nombre', 
        required=True, 
        translate=True,
        help="Descripción completa de la acción"
    )
    active = fields.Boolean(
        string='Activo', 
        default=True,
        help="Indica si esta acción está disponible para su uso"
    )
    sequence = fields.Integer(
        string='Secuencia',
        default=10,
        help="Define el orden de visualización"
    )
    is_system_action = fields.Boolean(
        string='Acción del Sistema',
        default=False,
        help="Marcar si es una acción generada automáticamente por el sistema"
    )
    requires_approval = fields.Boolean(
        string='Requiere Aprobación',
        default=False,
        help="Indica si esta acción necesita aprobación para ejecutarse"
    )
    
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
        ('code_unique', 'UNIQUE(code)', 'El código de la acción debe ser único!'),
    ]