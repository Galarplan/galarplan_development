# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountSavingPlan(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'account.saving.plan'
    _description = 'Plantilla de Planes de ahorro'

    saving_type = fields.Selection([
        ('normal', 'normal'),
        ('ballon', 'Balón'),
    ], string='Tipo de ahorro', default='ahorro')
    name = fields.Integer(string='Nombre', required=True)
    periods = fields.Integer(string='Periodo')
    saving_amount    = fields.Monetary(string='Monto de ahorro')

    company_id = fields.Many2one(
        "res.company",
        string="Compañia",
        required=True,
        copy=False,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(related="company_id.currency_id",string='Moneda')

    journal_id = fields.Many2one('account.journal', string='Diario')

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('posted', 'Publicado'),
        ('cancel', 'Cancelado'),
    ], string='Estado', default='draft')

    document_type_id = fields.Many2one('l10n_latam.document.type', string='Tipo de Documento')

    fixed_amount = fields.Monetary(string='Cantidad Fija')
    quota_amount = fields.Monetary(string='Importe de la cuota')

    rate_inscription = fields.Float(string='Tasa de Inscripción')
    rate_expense = fields.Float(string='Tasa de gastos')
    rate_insurance = fields.Float(string='Tasa de seguro')
    rate_decrement_year = fields.Float(string='Decrecimiento de Tasa')

    _rec_name = "name"
    _order = "id desc"

    _check_company_auto = True



    


    
