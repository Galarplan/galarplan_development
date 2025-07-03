# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class AccountReportExpression(models.AbstractModel):
    _inherit = "account.report.expression"

    def _get_carryover_target_expression(self, options):
        return super()._get_carryover_target_expression(options)

    def name_get_code(self):
        return [(expr.id, f'{expr.report_line_name} [{expr.label}]') for expr in self]
