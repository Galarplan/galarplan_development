# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ResCompany(models.Model):
    _inherit = 'res.company'

    inscripcion_id = fields.Many2one("product.product", "Gasto de Inscripcion por Defecto")
    product_id = fields.Many2one("product.product", "Gasto de Producto por Defecto")
    seguro_id = fields.Many2one("product.product", "Gasto de Seguro por Defecto")
    ahorro_account_id = fields.Many2one("account.account", "Cuenta para Ahorros por Defecto")
    ahorro_journal_id= fields.Many2one("account.journal", "Diario para Ahorros por Defecto")
    payment_account_1 = fields.Many2one('account.account','cuenta por defecto banco')
    payment_account_2 = fields.Many2one('account.account','cuenta por defecto adjudicado')
    payment_account_3 = fields.Many2one('account.account','cuenta por defecto no adjudicado')