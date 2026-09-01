from odoo import models, api, _
from odoo.exceptions import UserError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def unlink(self):
        # Verificar si el usuario tiene el grupo de administración
        if not self.env.user.has_group('base.group_system'):
            raise UserError(_(
                '❌ Solo el administrador del sistema puede eliminar contactos.\n'
                'Si necesita eliminar este contacto, contacte al administrador.'
            ))
        
        return super(ResPartner, self).unlink()