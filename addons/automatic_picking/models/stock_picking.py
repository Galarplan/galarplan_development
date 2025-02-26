from odoo import models, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def create(self, vals):
        # Llama al método create original
        picking = super(StockPicking, self).create(vals)
        # Valida automáticamente el picking si cumple ciertas condiciones
        if picking.picking_type_id.code in ['outgoing', 'incoming']:  # Solo para entregas y recepciones
            picking.action_confirm()  # Confirma el picking
            picking.action_assign()   # Asigna los productos
            if all(move.state == 'assigned' for move in picking.move_ids):  # Verifica que todos los movimientos estén asignados
                picking.button_validate()  # Valida el picking
        return picking