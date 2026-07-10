from odoo import models, fields, api

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    x_comentario = fields.Char(
        string='Comentario',
        size=100,  # máximo 100 caracteres
    )
    @api.onchange('product_id', 'x_comentario')
    def _onchange_producto_comentario(self):
        for line in self:
            if not line.product_id:
                continue

            # Descripción estándar que Odoo coloca en la factura
            descripcion = line.product_id.get_product_multiline_description_sale()

            # Si existe comentario, lo concatena
            if line.x_comentario:
                descripcion = f"{descripcion} {line.x_comentario}"

            line.name = descripcion