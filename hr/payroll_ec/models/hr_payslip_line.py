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

    provision_rule_ids=fields.Integer("rules",relation=None)
    historic_line_id = fields.Many2one("hr.employee.historic.lines", "Historico de Empleado")

    @api.onchange('total')
    @api.depends('total')
    def _compute_abs_total(self):
        DEC = 2
        for brw_each in self:
            brw_each.abs_total = round(abs(brw_each.total or 0.00), DEC)

    def create_historic_line(self):
        OBJ_HISTORIC = self.env["hr.employee.historic.lines"]
        for brw_each in self:
            vals = {
                "payslip_line_id": brw_each.id,
                "payslip_id": brw_each.slip_id.id,
                "employee_id": brw_each.slip_id.employee_id.id,
                "contract_id": brw_each.slip_id.contract_id.id,
                "company_id": brw_each.slip_id.company_id.id,
                "grouped": False,
                "month_id": brw_each.slip_id.payslip_run_id.month_id.id,
                "year": brw_each.slip_id.payslip_run_id.year,
                "amount": brw_each.abs_total,
                "rule_id": brw_each.salary_rule_id.id,
                "state": "draft"
            }
            if not brw_each.historic_line_id:
                brw_historic_line = OBJ_HISTORIC.create(vals)
                brw_each.historic_line_id = brw_historic_line.id
            else:
                brw_each.historic_line_id.write(vals)
        return True

    def action_historic_posted(self):
        for brw_each in self:
            brw_historic_line = brw_each.historic_line_id
            if brw_historic_line:
                brw_historic_line.action_posted()
        return True

    def action_historic_draft(self):
        for brw_each in self:
            brw_historic_line = brw_each.historic_line_id
            if brw_historic_line:
                brw_historic_line.action_draft()
        return True

    def unlink_history(self):
        for brw_each in self:
            brw_historic_line = brw_each.historic_line_id
            if brw_historic_line:
                brw_historic_line.unlink()
        return True