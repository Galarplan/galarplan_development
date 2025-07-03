# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api

class account_move_line(models.Model):
    _inherit = 'account.move.line'

    level_code = fields.Integer(string='Nivel', compute='_compute_level_code', store=True)

    @api.depends('account_id','account_id.code')
    def _compute_level_code(self):
        for record in self:
            if record.account_id and record.account_id.code[0].isdigit():
                record.level_code = int(record.account_id.code[0])
            else:
                record.level_code = 0
