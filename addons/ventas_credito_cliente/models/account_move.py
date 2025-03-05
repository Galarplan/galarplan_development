from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AccountMove(models.Model):
    _inherit = "account.move"

    is_credit_sale = fields.Boolean(string="Venta a Crédito")
    is_credit_bank = fields.Boolean(string="Venta por financiento banco")
    is_direct = fields.Boolean(string="Venta Por contado")
    is_galarplan = fields.Boolean(string="Venta Clientes Galarplan")

    def action_post(self):
        """Al confirmar la factura, usa la cuenta contable de crédito configurada en el cliente si es una venta a crédito."""
        for move in self:
            if move.is_credit_sale:
                if not move.partner_id.property_account_receivable_credit_id:
                    raise ValidationError(_("El cliente no tiene configurada una cuenta de crédito en su ficha. Configúrela antes de continuar."))
                for line in move.line_ids.filtered(lambda l: l.account_id == move.partner_id.property_account_receivable_id):
                    line.account_id = move.partner_id.property_account_receivable_credit_id  # Usa la cuenta configurada en el cliente

            if move.is_credit_bank:
                if not move.partner_id.property_account_financial_bank_id:
                    raise ValidationError(_("El cliente no tiene configurada una cuenta de financiamiento por banco en su ficha. Configúrela antes de continuar."))
                for line in move.line_ids.filtered(lambda l: l.account_id == move.partner_id.property_account_receivable_id):
                    line.account_id = move.partner_id.property_account_financial_bank_id  # Usa la cuenta configurada en el cliente


            if move.is_direct:
                if not move.partner_id.property_account_direct_funds_id:
                    raise ValidationError(_("El cliente no tiene configurada una cuenta de contado en su ficha. Configúrela antes de continuar."))
                for line in move.line_ids.filtered(lambda l: l.account_id == move.partner_id.property_account_receivable_id):
                    line.account_id = move.partner_id.property_account_direct_funds_id  # Usa la cuenta configurada en el cliente


            if move.is_galarplan:
                if not move.partner_id.propoerty_account_adjudicated_id:
                    raise ValidationError(_("El cliente no tiene configurada una cuenta de facturacion a cliente de galarplan en su ficha. Configúrela antes de continuar."))
                for line in move.line_ids.filtered(lambda l: l.account_id == move.partner_id.property_account_receivable_id):
                    line.account_id = move.partner_id.propoerty_account_adjudicated_id  # Usa la cuenta configurada en el cliente            
        
        return super().action_post()
