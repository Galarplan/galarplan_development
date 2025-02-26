# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AccountMove(models.Model):
    _inherit = 'account.move'

    saving_line_id=fields.Many2one("account.saving.lines","Origen de Plan de Ahorro",required=False)
    saving_id = fields.Many2one("account.saving", "Plan de Ahorro", required=False)

    @api.model
    def create(self, vals):
        if 'saving_line_id' in vals and vals['saving_line_id']:
            existing_move = self.env['account.move'].search([
                ('saving_line_id', '=', vals['saving_line_id'])
            ], limit=1)
            if existing_move:
                raise ValidationError("Ya existe un asiento contable con este valor de 'saving_line_id'.")

        return super(AccountMove, self).create(vals)