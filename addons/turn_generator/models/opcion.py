from odoo import models, fields,api

class Opcion(models.Model):
    _name = 'generador_turnos.opcion'
    _description = 'Opción'

    nombre = fields.Char(string='Nombre', required=True)
    descripcion = fields.Text(string='Descripción')
    imagen = fields.Binary(string='Imagen', attachment=True)
    imagen_id = fields.Integer()
    slug = fields.Char(string='Slug')



    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, record.nombre))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        domain = args + [('nombre', operator, name)]
        records = self.search(domain, limit=limit)
        return records.name_get()