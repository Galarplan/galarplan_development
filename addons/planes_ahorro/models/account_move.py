# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AccountMove(models.Model):
    _inherit = 'account.move'

    saving_line_id=fields.Many2one("account.saving.lines","Origen de Plan de Ahorro",required=False,copy=False)
    saving_id = fields.Many2one("account.saving", "Plan de Ahorro", required=False,copy=False)
    plan_ahorro_move_id = fields.Many2one("account.move", string="# Asiento Plan de Ahorro",copy=False)
    plan_ahorro_move_line_ids = fields.One2many(related="plan_ahorro_move_id.line_ids", string="Lineas de # Asiento Plan de Ahorro",store=False,readonly=True,copy=False)

    def button_draft(self):
        for move in self:
            if move.plan_ahorro_move_id:
                super(AccountMove, move.plan_ahorro_move_id).button_draft()
        return super(AccountMove,self).button_draft()

    def action_post(self):
        for move in self:
            if move.plan_ahorro_move_id:
                super(AccountMove, move.plan_ahorro_move_id).action_post()
            if move.move_type=='out_refund' and move.reversed_entry_id and move.saving_line_id:
                move.saving_line_id.invoice_id=False
        return super(AccountMove,self).action_post()

    def button_cancel(self):
        for move in self:
            if move.plan_ahorro_move_id:
                super(AccountMove, move.plan_ahorro_move_id).button_cancel()
        return super(AccountMove,self).button_cancel()

    def unlink(self):
        for brw_each in self:
            if brw_each.state!='draft':
                raise ValidationError(_("No puedes eliminar un documento que no este en estado preliminar"))
            if brw_each.plan_ahorro_move_id:
                brw_each.plan_ahorro_move_id.button_draft()
                super(AccountMove, brw_each.plan_ahorro_move_id).unlink()
        return super(AccountMove,self).unlink()

    @api.model
    def create(self, vals):
        # if 'saving_line_id' in vals and vals['saving_line_id']:
        #     existing_move = self.env['account.move'].search([
        #         ('saving_line_id', '=', vals['saving_line_id']),
        #         ('move_type', '=', vals['move_type']),
        #     ], limit=1)
        #     if existing_move:
        #         raise ValidationError("Ya existe un asiento contable con este valor de 'saving_line_id'.")

        return super(AccountMove, self).create(vals)

    def _l10n_ec_get_payment_data(self):
        """ Get payment data for the XML.  """
        payment_data = []
        pay_term_line_ids = self.line_ids.filtered(
            lambda line: line.account_id.account_type in ('asset_receivable', 'liability_payable') and not line.for_planes
        )
        for line in pay_term_line_ids:
            payment_vals = {
                'payment_code': self.l10n_ec_sri_payment_id.code,
                'payment_total': abs(line.balance),
            }
            if self.invoice_payment_term_id and line.date_maturity and  not line.for_planes:
                payment_vals.update({
                    'payment_term': max(((line.date_maturity - self.invoice_date).days), 0),
                    'time_unit': "dias",
                })
            payment_data.append(payment_vals)
        return payment_data
