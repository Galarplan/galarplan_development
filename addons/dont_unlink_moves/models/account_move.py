from odoo import _, api, fields, models
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = 'account.move'

    def unlink(self):
        # Levantar error para evitar cualquier eliminación
        raise UserError(_('No está permitido eliminar asientos contables. Esta Accion Sera Reportada al administrador.'))
        
        # El return nunca se ejecutará por el raise, pero se mantiene por convención
        return super(AccountMove, self).unlink()