# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

from collections import defaultdict

from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError, ValidationError, AccessError, RedirectWarning
from odoo.tools.misc import clean_context
from odoo.tools import (
    date_utils,
    email_re,
    email_split,
    float_compare,
    float_is_zero,
    float_repr,
    format_amount,
    format_date,
    formatLang,
    frozendict,
    get_lang,
    groupby,
    is_html_empty,
    sql
)

from odoo.addons.account.models.account_move import AccountMove as BaseAccountMove
from odoo.addons.account.models.account_move import TYPE_REVERSE_MAP

def _new_reverse_moves(self, default_values_list=None, cancel=False):
    ''' Reverse a recordset of account.move.
    If cancel parameter is true, the reconcilable or liquidity lines
    of each original move will be reconciled with its reverse's.
    :param default_values_list: A list of default values to consider per move.
                                ('type' & 'reversed_entry_id' are computed in the method).
    :return:                    An account.move recordset, reverse of the current self.
    '''
    if not default_values_list:
        default_values_list = [{} for move in self]

    if cancel:
        lines = self.mapped('line_ids')
        # Avoid maximum recursion depth.
        if lines:
            lines.remove_move_reconcile()

    reverse_moves = self.env['account.move']
    for move, default_values in zip(self, default_values_list):
        default_values.update({
            'move_type': TYPE_REVERSE_MAP[move.move_type],
            'reversed_entry_id': move.id,
            'partner_id': move.partner_id.id,
        })
        reverse_moves += move.with_context(
            move_reverse_cancel=cancel,
            include_business_fields=True,
            skip_invoice_sync=move.move_type == 'entry',
        ).copy(default_values)

    reverse_moves.with_context(skip_invoice_sync=cancel).write({'line_ids': [
        Command.update(line.id, {
            'balance': -line.balance,
            'amount_currency': -line.amount_currency,
        })
        for line in reverse_moves.line_ids
        if line.move_id.move_type == 'entry' or line.display_type in ('cogs', 'planes')
    ]})

    # Reconcile moves together to cancel the previous one.
    if cancel:
        reverse_moves.with_context(move_reverse_cancel=cancel)._post(soft=False)
        for move, reverse_move in zip(self, reverse_moves):
            group = defaultdict(list)
            for line in (move.line_ids + reverse_move.line_ids).filtered(lambda l: not l.reconciled):
                group[(line.account_id, line.currency_id)].append(line.id)
            for (account, dummy), line_ids in group.items():
                if account.reconcile or account.account_type in ('asset_cash', 'liability_credit_card'):
                    self.env['account.move.line'].browse(line_ids).with_context(move_reverse_cancel=cancel).reconcile()

    return reverse_moves


# inyectar directamente
BaseAccountMove._reverse_moves = _new_reverse_moves

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
