from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    seller_id = fields.Many2one(
        comodel_name='hr.employee',  # Relacionado con los usuarios del sistema (vendedores)
        string='Vendedor',
        help='Usuario que realizó la venta asociada a esta factura.'
    )
    
