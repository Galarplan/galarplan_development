# models/stock_picking.py

from odoo import models, fields, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    account_move_ids = fields.Many2many(
        'account.move',
        string='Asientos contables',
        compute='_compute_account_move_ids',
        store=False
    )

    def _compute_account_move_ids(self):
        for picking in self:
            account_moves = self.env['account.move']
            for move in picking.move_ids:
                valuation_layers = self.env['stock.valuation.layer'].search([('stock_move_id', '=', move.id)])
                account_moves |= valuation_layers.mapped('account_move_id')
            picking.account_move_ids = account_moves
