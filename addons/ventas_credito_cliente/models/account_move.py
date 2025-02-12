from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AccountMove(models.Model):
    _inherit = "account.move"

    is_credit_sale = fields.Boolean(string="Venta a Crédito")

    def action_post(self):
        """Al confirmar la factura, usa la cuenta contable de crédito configurada en el cliente si es una venta a crédito."""
        for move in self:
            if move.is_credit_sale:
                if not move.partner_id.property_account_receivable_credit_id:
                    raise ValidationError(_("El cliente no tiene configurada una cuenta de crédito en su ficha. Configúrela antes de continuar."))
                for line in move.line_ids.filtered(lambda l: l.account_id == move.partner_id.property_account_receivable_id):
                    line.account_id = move.partner_id.property_account_receivable_credit_id  # Usa la cuenta configurada en el cliente
        
        return super().action_post()
