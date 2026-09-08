from odoo import _, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    def unlink(self):

        # Permitir eliminaciones internas de Odoo
        # durante procesos como ROMPER CONCILIACIÓN
        if self.env.context.get('force_delete'):
            return super(AccountMove, self).unlink()

        # Bloquear eliminación manual de asientos
        raise UserError(
            _(
                'No está permitido eliminar asientos contables. '
                'Esta Acción Será Reportada al administrador.'
            )
        )