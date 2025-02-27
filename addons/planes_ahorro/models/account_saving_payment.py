# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AccountSavingPayment(models.Model):
    _name = 'account.saving.payment'
    _description = 'Pago Migrado'

    saving_id = fields.Many2one('account.saving', string='Plan de ahorro', ondelete="cascade")
    saving_line_id = fields.Many2one('account.saving.lines', string='Detalle de Plan de ahorro', ondelete="cascade")


    currency_id = fields.Many2one(related="saving_id.currency_id", string='Moneda', store=False, readonly=True)
    type = fields.Selection([('payment', 'Pago'), ('historic', 'Historico')], default="payment", string="Tipo",
                            required=True)
    payment_journal_name = fields.Char("Diario")
    payment_date = fields.Date("Fecha")
    payment_ref = fields.Char("Referencia")
    amount = fields.Monetary(string="Monto")
    old_ref_id = fields.Char("Antiguo REF ID", tracking=True)
    payment_state = fields.Selection([('draft', 'Preliminar'),
                                      ('posted', 'Publicado'),
                                      ('cancel', 'Anulado'),
                                      ], "Estado")
    line_ids=fields.One2many("account.saving.line.payment","old_payment_id","Detalle de Pago")

    _rec_name="payment_ref"