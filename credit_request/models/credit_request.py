# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

ACCOUNT_TYPE = [('savings','Savings'),('checking','Checking')]
CHECKING_TYPE = [('01','6 months'),('02','1 year'),('03','Bank Certificate')]
PROVIDERS_TIME = [('01','6 months'),('02','1 year')]
class CreditRequest(models.AbstracModel):
    _name = "credit.request.abstract"
    _descripcion = "Credit Request"

    name = fields.Char(string="Reference", required=True, default=_("Nuevo"))
    boss_id = fields.Many2one('hr.employee',string='Boss')
    brand = fields.Many2one("fleet.vehicle.model.brand", string="brand")
    model = fields.Many2one("fleet.vehicle.model", string="model")
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )
    amount = fields.Monetary(string="Price")
    start_amount_price = fields.Monetary(string="Start Price")
    start_amount_difference_price = fields.Monetary(string="Start Price Difference")
    time = fields.Integer(string="time")
    uses = fields.Char(string="Uses")
    device = fields.Char(string="Device")
    legal_costs = fields.Char(string="Legal Cost")
    approved_time = fields.Integer(string="Approved Time")
    approved_fee = fields.Float(string="Approved Fee")
    condition = fields.Char(string="Condition")
    approved_by = fields.Many2one("hr.employee", string="Approved By")

    bank_account_ids = fields.One2many(
        "res.partner.bank", "credit_request_id", string="Bank Accounts"
    )

    credit_card_ids = fields.One2many('credit.cards','credit_card_id',string ='credit cards')

    provider_request_ids = fields.One2many('provider.credit.request','provider_credit_request_id', string='providers')


    providers_time = fields.Selection(PROVIDERS_TIME,string='providers time')    
    checking_account_time = fields.Selection(CHECKING_TYPE,string='Checking time')

    is_main_provider = fields.Boolean(string='is main provider', default=False)
    
    credit_type = fields.Selection(
        [("natural", "Persona Natural"), ("juridica", "Persona Jurídica")],
        string="Type",
        required=True,
    )
    
    
    request_date = fields.Date(string="Request Date", default=fields.Date.context_today)




    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        default="draft",
    )

    # Additional Fields
    seller_id = fields.Many2one("", string="Seller")
    vehicle_details = fields.Text(string="Vehicle Details")
    observations = fields.Text(string="Observations")


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    credit_request_id = fields.Many2one('credit.request', string="Credit Request", ondelete='cascade')
    acc_type = fields.Selection(ACCOUNT_TYPE,default='savings')

class RedCreditCard(models.Model):
    _name = 'credit.cards'
    _description = 'credit cards client'

    credit_card_id = fields.Many2one('credit.request', string='Credit request', ondelete='cascade')
    bank = fields.Many2one('res.bank', string='bank')
    credit_number = fields.Char(string='Credit number',size=16)
    expiration_month = fields.Char(string='Expiration Month', size=2)
    expiration_year = fields.Char(string='Expiration Month', size=4)
    amount = fields.Integer(string='amount')


class ProviderCreditRequest(models.Model):
    _name = 'provider.credit.request'
    _description = ' provider lines'

    provider_credit_request_id = fields.Many2one('credit.request', string='Credit request', ondelete='cascade')

    company_name = fields.Char(string='Company')
    address = fields.Char(string='company address')
    contact_name = fields.Char(string='Contact Name')
    contact_number = fields.Char(string='Contact Number')


    

