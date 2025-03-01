from odoo import models, fields

class ResPartner(models.Model):
    _inherit = "res.partner"

    property_account_receivable_credit_id = fields.Many2one(
        "account.account",
        string="Cuenta por Cobrar a Crédito",
        company_dependent=True,
        help="Cuenta contable para ventas a crédito de este cliente.",
    )

    property_account_financial_bank_id = fields.Many2one(
        "account.account",
        string="Cuenta por Cobrar Financiamiento Banco",
        company_dependent=True,
        help="Cuenta contable para ventas por finaciamiento de banco.",
    )

    property_account_direct_funds_id = fields.Many2one(
        "account.account",
        string="Cuenta por Cobrar Contado",
        company_dependent=True,
        help="Cuenta contable para ventas por Contado.",
    )

    propoerty_account_adjudicated_id = fields.Many2one (
        "account.account",
        string="Cuenta por Cobrar Clientes Galarplan",
        company_dependent=True,
        help="Cuenta contable para ventas por clientes de galarplan.",
    )
    