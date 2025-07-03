# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api

class AccountAccount(models.Model):
    _inherit = 'account.account'

    level_code = fields.Integer(string='Nivel', compute='_compute_level_code', store=True)

    @api.depends('code')
    def _compute_level_code(self):
        for record in self:
            if record.code and record.code[0].isdigit():
                record.level_code = int(record.code[0])
            else:
                record.level_code = 0
