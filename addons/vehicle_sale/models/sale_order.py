from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_vehicle = fields.Boolean(string="Es Vehículo")

    def _prepare_invoice(self):
        vals = super()._prepare_invoice()

        vals['is_vehicle'] = self.is_vehicle

        return vals