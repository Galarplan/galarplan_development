from odoo import models, exceptions

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        for move in self:
            # Verificar si el partner está verificado
            if move.partner_id and not move.partner_id.cliente_proveedor_verificado:
                raise exceptions.ValidationError(
                    f"El cliente/proveedor {move.partner_id.name} no está verificado. "
                    "Por favor, verifique al cliente/proveedor antes de publicar el asiento."
                )
        # Si todo está bien, llamar al método original
        return super(AccountMove, self).action_post()