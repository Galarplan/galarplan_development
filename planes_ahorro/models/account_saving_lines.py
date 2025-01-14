# -*- coding: utf-8 -*-

from odoo import models, fields, api, _



class AccountSavingLines(models.Model):
    _name = 'account.saving.lines'
    _description = 'listado de cuotas para planes de ahorro'

    sequence=fields.Integer("# Secuencia",required=True)
    saving_id = fields.Many2one('account.saving', string='Plan de ahorro')
    currency_id = fields.Many2one(related="saving_id.currency_id", string='Moneda',store=False,readonly=True)
    number = fields.Integer(string='Número de cuota')
    date = fields.Date(string='Fecha de cuota')
    saving_amount = fields.Monetary(string='Aportaciones')
    principal_amount=fields.Monetary(string='Planes de Ahorro')
    pagos = fields.Monetary(string='Pagos')
    pendiente = fields.Monetary(string='Pendiente')
    estado_pago = fields.Selection([ ('pendiente', 'Pendiente'), ('pagado', 'Pagado')], string='Estado de pago', default='pendiente')