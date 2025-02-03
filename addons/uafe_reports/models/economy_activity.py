from odoo import models, fields, api


class EconomyActivity(models.Model):
    _name = 'economy.activity'
    _description = 'Actividad economica'

    name = fields.Char(string='Nombre de la actividad')
    code = fields.Char(string='Codigo')
    active = fields.Boolean(string='Activo', default = True)

    def name_get(self):
        """Devuelve el nombre del registro en formato 'Código - Nombre'."""
        result = []
        for record in self:
            name = f"{record.code or ''} - {record.name or ''}"
            result.append((record.id, name))
        return result
    
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Permite buscar por código o nombre."""
        args = args or []
        domain = ['|', ('name', operator, name), ('code', operator, name)]
        records = self.search(domain + args, limit=limit)
        return records.name_get()