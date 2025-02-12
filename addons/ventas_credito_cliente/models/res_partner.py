from odoo import models, fields

class ResPartner(models.Model):
    _inherit = "res.partner"

    property_account_receivable_credit_id = fields.Many2one(
        "account.account",
        string="Cuenta por Cobrar a Crédito",
        company_dependent=True,
        help="Cuenta contable para ventas a crédito de este cliente.",
    )