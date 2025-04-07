# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

# from odoo.odoo.api import ondelete


class report_view_general_ledger_line(models.Model):
    _name = 'report.view.general.ledger.line'
    _description = 'Detalle reporte Mayor'

    report_id = fields.Many2one('report.view.general.ledger', string='General ledger', ondelete="cascade", readonly=True)
    date = fields.Date(string='Fecha', required=True)
    partner_id = fields.Many2one('res.partner', string='Empresa', required=False, readonly=True)
    journal_id = fields.Many2one('account.journal', string='Diario', required=False, readonly=True)
    name = fields.Char('Referencia', required=True)
    debit = fields.Float('Debe', default=0)
    credit = fields.Float('Haber', default=0)
    amount_accumulated = fields.Float('Acumulado', default=0)
