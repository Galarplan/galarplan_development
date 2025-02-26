from odoo import models, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        # Llama al método action_confirm original
        res = super(SaleOrder, self).action_confirm()
        # Valida automáticamente los pickings asociados
        for order in self:
            for picking in order.picking_ids:
                picking.action_confirm()
                picking.action_assign()
                if all(move.state == 'assigned' for move in picking.move_ids):
                    picking.button_validate()
        return res