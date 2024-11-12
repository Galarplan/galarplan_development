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