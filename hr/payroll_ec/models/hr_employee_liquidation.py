# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import ValidationError
from odoo.tools.config import config


class HrEmployeeLiquidation(models.Model):
    _inherit = "hr.employee.document"
    _name = "hr.employee.liquidation"
    _description = "Liquidacion de Empleados"

    @api.model
    def get_default_category_code(self):
        return self._context.get("default_category_code", None)

    @api.model
    def get_default_category_id(self):
        code = self.get_default_category_code()
        srch_code = self.env["hr.salary.rule.category"].sudo().search([('code', '=', code)])
        return srch_code and srch_code[0].id or False

    company_id = fields.Many2one(
        "res.company",
        string="Compañia",
        required=True,
        copy=False,
        default=lambda self: self.env.company,
    )

    total = fields.Monetary(store=True, compute="_compute_total")

    total_to_paid = fields.Monetary(store=True, compute="_compute_total")
    total_paid = fields.Monetary(store=True, compute="_compute_total")
    total_pending = fields.Monetary(store=True, compute="_compute_total")

    type=fields.Selection([('liquidation','Finiquito'),
                           ('vacation','Vacacion')],string="Tipo",required=True,default="liquidation")

    category_code = fields.Char(string="Código de Categoría", required=False, default=get_default_category_code)
    category_id = fields.Many2one("hr.salary.rule.category", string="Categoría", default=get_default_category_id)
    rule_id = fields.Many2one("hr.salary.rule", string="Rubro", required=False)

    name=fields.Char(string="Descripcion",compute="_compute_name",store=True,readonly=False)

    period_vacation_id=fields.Many2one("hr.vacation.period","Periodo")

    vacation_request_ids=fields.Many2many("hr.leave","liquidation_vacations_rels","liquidation_id","vacation_id",string="Permisos")
    pending_days = fields.Integer("Pendiente(s)", default=0 )
    attempt_pending_days = fields.Integer("P. Tentativos(s)", default=0 )
    attempt_days = fields.Integer("Dias Tentativos",   default=0)
    days = fields.Integer("Dia(s)",  default=0)

    provision_ids = fields.Many2many("hr.employee.historic.lines", "liquidation_historic_lines", "liquidation_id",
                                     "line_id", "Provisiones")


    _check_company_auto = True

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id:
            srch=self.env["hr.contract"].sudo().search([('employee_id','=',self.employee_id.id),
                                                        ('company_id', '=', self.company_id.id),
                                                        ('state','=','open')
                                                        ])
            self.contract_id = srch and srch[0].id or False
            return
        self.contract_id=False

    @api.onchange('contract_id')
    def onchange_contract_id(self):
        if self.contract_id:
            self.department_id = self.contract_id.department_id and self.contract_id.department_id[0].id or False
            self.job_id = self.contract_id.job_id and self.contract_id.job_id[0].id or False
            return
        self.department_id = False
        self.job_id = False

    @api.onchange('contract_id','type','contract_id.date_start','contract_id.date_end')
    @api.depends('contract_id', 'type','contract_id.date_start','contract_id.date_end')
    def _compute_name(self):
        for brw_each in self:
            name="%s DE %s PERIODO(%s AL %s)" % ((brw_each.type=='liquidation') and "FINIQUITO" or "VACACIONES",
                               brw_each.contract_id.employee_id.name,
                               brw_each.contract_id.date_start,brw_each.contract_id.date_end or '')
            brw_each.name=name

    @api.onchange('contract_id','type','period_vacation_id')
    def onchange_for_type(self):
        provision_ids=[]
        vacation_request_ids=[]
        pending_days,attempt_pending_days,attempt_days,days=0,0,0,0
        if self.type=='vacation':
            if self.contract_id and self.period_vacation_id:
                date_from=self.period_vacation_id.date_start
                date_end = self.period_vacation_id.date_end
                self._cr.execute("""select hhl.id,hhl.id from hr_employee_historic_lines hhl
inner join hr_employee he on he.id=hhl.employee_id
where 
	 (   hhl.date_from>=%s and hhl.date_to<=%s   )
		and hhl.employee_id=%s and hhl.state='posted'
		  and hhl.rule_id=%s
		  """,(date_from,date_end,self.employee_id.id,self.env.ref("payroll_ec.rule_PROV_VACACIONES").id ))
                result=self._cr.fetchall()

                provision_ids=result and [*dict(result)] or []
                pending_days=self.period_vacation_id.pending_days
                attempt_pending_days = self.period_vacation_id.attempt_pending_days
                attempt_days = self.period_vacation_id.attempt_days
                days = self.period_vacation_id.days
                vacation_request_ids=self.period_vacation_id.request_ids.ids

        self.provision_ids=[(6,0,provision_ids)]

        self.pending_days=pending_days
        self.attempt_pending_days = attempt_pending_days
        self.attempt_days = attempt_days
        self.days =days
        self.vacation_request_ids=[(6,0,vacation_request_ids)]

    @api.onchange('contract_id','provision_ids','type')
    @api.depends('contract_id', 'provision_ids','type')
    def _compute_total(self):
        DEC=2
        for brw_each in self:
            total=0.00
            total_to_paid=0.00
            total_paid=0.00
            total_pending=0.00
            if brw_each.type=='vacation':
                for brw_provision in brw_each.provision_ids:
                    total+=brw_provision.amount
                    total_to_paid += brw_provision.amount_to_paid
                    total_paid += brw_provision.amount_paid
                    total_pending += brw_provision.amount_residual
            brw_each.total=round(total,DEC)
            brw_each.total_to_paid =round( total_to_paid,DEC)
            brw_each.total_paid = round(total_paid,DEC)
            brw_each.total_pending = round(total_pending,DEC)