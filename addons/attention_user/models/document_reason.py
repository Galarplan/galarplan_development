from odoo import models, fields, api, _

class DocumentReason(models.Model):
    _name = 'document.reason'
    _description = 'Razones de Documentos'
    _order = 'name asc'
    
    code = fields.Char(
        string='Código', 
        required=True,
        help="Código único para identificar la razón del documento"
    )
    name = fields.Char(
        string='Nombre', 
        required=True, 
        translate=True,
        help="Descripción completa de la razón del documento"
    )
    active = fields.Boolean(
        string='Activo', 
        default=True,
        help="Indica si esta razón está disponible para su uso"
    )
    document_type = fields.Selection(
        selection=[
            ('internal', 'Uso Interno'),
            ('external', 'Uso con Clientes'),
            ('both', 'Ambos usos')
        ],
        string='Tipo de Documento',
        default='both',
        required=True
    )
    requires_evidence = fields.Boolean(
        string='Requiere Evidencia',
        default=False,
        help="Marcar si este tipo de documento siempre requiere evidencia adjunta"
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
        ('code_unique', 'UNIQUE(code)', 'El código de la razón debe ser único!'),
    ]