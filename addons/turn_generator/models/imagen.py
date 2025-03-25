from odoo import models, fields

class Imagen(models.Model):
    _name = 'generador_turnos.imagen'
    _description = 'Imagen'

    nombre = fields.Char(string='Nombre', required=True)
    descripcion = fields.Text(string='Descripción')
    imagen = fields.Binary(string='Imagen', attachment=True)


    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, record.nombre))
        return result

    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        domain = args + [('nombre', operator, name)]
        return self.search(domain, limit=limit).name_get()