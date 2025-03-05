# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AccountMove(models.Model):
    _inherit = 'account.move'

    saving_line_id=fields.Many2one("account.saving.lines","Origen de Plan de Ahorro",required=False)
    saving_id = fields.Many2one("account.saving", "Plan de Ahorro", required=False)
    plan_ahorro_move_id = fields.Many2one("account.move", string="# Asiento Plan de Ahorro")
    plan_ahorro_move_line_ids = fields.One2many(related="plan_ahorro_move_id.line_ids", string="Lineas de # Asiento Plan de Ahorro",store=False,readonly=True)

    def button_draft(self):
        for move in self:
            if move.plan_ahorro_move_id:
                super(AccountMove, move.plan_ahorro_move_id).button_draft()
        return super(AccountMove,self).button_draft()

    def action_post(self):
        for move in self:
            if move.plan_ahorro_move_id:
                super(AccountMove, move.plan_ahorro_move_id).action_post()
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
        if 'saving_line_id' in vals and vals['saving_line_id']:
            existing_move = self.env['account.move'].search([
                ('saving_line_id', '=', vals['saving_line_id']),
                ('move_type', '=', vals['move_type']),
            ], limit=1)
            if existing_move:
                raise ValidationError("Ya existe un asiento contable con este valor de 'saving_line_id'.")

        return super(AccountMove, self).create(vals)

