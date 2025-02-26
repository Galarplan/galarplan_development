from odoo import models, api
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    from odoo import models, api
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_confirm(self):
        # Verificar disponibilidad antes de confirmar la orden de compra
        for order in self:
            for line in order.order_line:
                product = line.product_id
                if product.type == 'product':  # Solo para productos almacenables
                    available_qty = product.qty_available  # Cantidad disponible en el inventario
                    if available_qty >= line.product_qty:  # Si ya hay suficiente stock
                        raise UserError(
                            f"El producto {product.name} ya tiene suficiente stock. "
                            f"Disponible: {available_qty}, Solicitado: {line.product_qty}. "
                            f"No es necesario realizar la compra."
                        )
        # Si no hay suficiente stock, confirmar la orden de compra
        return super(PurchaseOrder, self).button_confirm()