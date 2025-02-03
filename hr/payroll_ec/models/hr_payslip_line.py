# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api,fields, models,_
from odoo.exceptions import ValidationError,UserError
from ...calendar_days.tools import CalendarManager,DateManager,MonthManager

dtObj = DateManager()

class HrPayslipLine(models.Model):
    _inherit="hr.payslip.line"

    _order="category_id asc,amount desc"

    category_code=fields.Char(related="category_id.code",store=False,readonly=True)

    abs_total = fields.Monetary("ABS Total",store=True,digits=(16,2), compute="_compute_abs_total")

    company_id = fields.Many2one(related="slip_id.company_id", store=False, readonly=True)
    currency_id = fields.Many2one(related="company_id.currency_id", store=False, readonly=True)
    @api.onchange('total')
    @api.depends('total')
    def _compute_abs_total(self):
        DEC=2
        for brw_each in self:
            brw_each.abs_total=round(abs(brw_each.total or 0.00),DEC)