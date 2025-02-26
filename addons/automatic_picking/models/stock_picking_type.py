from odoo import models, api
from odoo.exceptions import UserError
from odoo.tools.translate import _

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    def action_assign(self):
        """
        Sobrescribe completamente la función action_assign para implementar lógica personalizada.
        """
        # Lógica personalizada
        print("Ejecutando lógica personalizada en action_assign")

        # Verificar si hay movimientos para procesar
        pickings = self.env['stock.picking'].search([('picking_type_id', '=', self.id)])
        moves = pickings.mapped('move_ids').filtered(
            lambda move: move.state not in ('cancel', 'done')
        )
        if not moves:
            raise UserError(_('No hay movimientos para verificar la disponibilidad.'))

        # Asignar las cantidades disponibles (lógica personalizada)
        for move in moves:
            move._action_assign()  # Llama a la lógica de asignación de movimientos

        # Lógica adicional después de asignar los movimientos
        assigned_pickings = self.env['stock.picking'].search([
            ('picking_type_id', '=', self.id),
            ('state', '=', 'assigned')
        ])
        if assigned_pickings:
            self.message_post(body="Los pickings de este tipo han sido asignados correctamente.")

        return True