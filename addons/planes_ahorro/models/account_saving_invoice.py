# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AccountSavingInvoice(models.Model):
    _name = 'account.saving.invoice'
    _description = 'Factura Migrada'

    saving_id = fields.Many2one('account.saving', string='Plan de ahorro', ondelete="cascade")
    saving_line_id = fields.Many2one('account.saving.lines', string='Detalle de Plan de ahorro', ondelete="cascade")

    currency_id = fields.Many2one(related="saving_id.currency_id", string='Moneda', store=False, readonly=True)
    type = fields.Selection([('out_invoice', 'Factura'), ('out_refund', 'NC')], default="out_invoice", string="Tipo",
                            required=True)
    invoice_date = fields.Date("Fecha")
    invoice_ref = fields.Char("# Factura")
    amount = fields.Monetary(string="Total")
    old_ref_id = fields.Char("Antiguo REF ID", tracking=True)
    invoice_state = fields.Selection([('draft', 'Preliminar'),
                                      ('posted', 'Publicado'),
                                      ('cancel', 'Anulado'),
                                      ], "Estado")

    _rec_name="invoice_ref"