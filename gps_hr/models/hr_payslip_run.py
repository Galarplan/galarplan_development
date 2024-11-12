# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api,fields, models,_
from odoo.exceptions import ValidationError,UserError
from ...calendar_days.tools import CalendarManager,DateManager,MonthManager

dtObj = DateManager()
caObj=CalendarManager()

class HrPayslipRun(models.Model):
    _inherit="hr.payslip.run"

    @api.model
    def get_default_year(self):
        today = fields.Date.context_today(self)
        return today.year

    @api.model
    def get_default_month_id(self):
        today = fields.Date.context_today(self)
        srch=self.env["calendar.month"].sudo().search([('value','=',today.month)])
        return srch and srch[0].id or False

    @api.model
    def _get_default_company_id(self):
        if self._context.get("allowed_company_ids", []):
            return self._context.get("allowed_company_ids", [])[0]
        return False

    @api.model
    def _get_default_type_struct_id(self):
        srch=self.env["hr.payroll.structure.type"].sudo().search([])
        return srch and srch[0].id or False

    company_id = fields.Many2one("res.company", "Compañía", required=True, default=_get_default_company_id)
    currency_id = fields.Many2one(string="Moneda", related="company_id.currency_id", store=False, readonly=True)

    month_id = fields.Many2one("calendar.month", "Mes", required=True,default=get_default_month_id)
    year = fields.Integer("Año", required=True,default=get_default_year)

    total_in = fields.Monetary("Ingresos", digits=(16, 2), required=False, default=0.00, store=True,compute="_compute_total")
    total_out = fields.Monetary("Egresos", digits=(16, 2), required=False, default=0.00, store=True,compute="_compute_total")
    total_provision = fields.Monetary("Provisión", digits=(16, 2), required=False, default=0.00, store=True,compute="_compute_total")
    total = fields.Monetary("Total", digits=(16, 2), required=False, default=0.00, store=True, compute="_compute_total")

    type_struct_id=fields.Many2one("hr.payroll.structure.type","Tipo",required=True,default=_get_default_type_struct_id)

    move_line_ids=fields.One2many("hr.payslip.move","payslip_run_id","Detalle de Asiento")

    @api.depends('slip_ids', 'state')
    def _compute_state_change(self):
        pass

    @api.onchange('company_id','month_id','year','type_struct_id')
    def onchange_company_dates(self):
        name=None
        if self.company_id and self.month_id and self.year:
            name="NOMINA DE %s DEL %s PARA %s(%s)" % (self.month_id.name,self.year,self.company_id.name,self.type_struct_id and self.type_struct_id.name or '')
            name=name.upper()
        self.name = name
        self.slip_ids=[(5,)]

    @api.onchange('month_id','year')
    def onchange_year_month_id(self):
        if self.month_id and self.year:
            self.date_start=dtObj.create(self.year,self.month_id.value,1)
            self.date_end = dtObj.create(self.year, self.month_id.value, caObj.days(self.year,self.month_id.value))
        else:
            self.date_start=None
            self.date_end=None
        self.slip_ids=[(5,)]
        
    @api.onchange('slip_ids', 'slip_ids.total_in', 'slip_ids.total_out', 'slip_ids.total_provision',
                  'slip_ids.total_payslip')
    def onchange_line_ids(self):
        self._origin.update_total()

    @api.depends('slip_ids', 'slip_ids.total_in', 'slip_ids.total_out', 'slip_ids.total_provision',
                  'slip_ids.total_payslip')
    def _compute_total(self):
        for brw_each in self:
            brw_each.update_total()

    def update_total(self):
        DEC = 2
        for brw_each in self:
            total_in, total_out, total_provision, total = 0.00, 0.00, 0.00, 0.00
            for brw_line in brw_each.slip_ids:
                total_in += brw_line.total_in
                total_out += brw_line.total_out
                total_provision += brw_line.total_provision
                total += brw_line.total_payslip
            brw_each.total_in = round(total_in, DEC)
            brw_each.total_out = round(total_out, DEC)
            brw_each.total_provision = round(total_provision, DEC)
            brw_each.total = round(total, DEC)

    _order = "id desc"

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        raise ValidationError(_("No puedes duplicar este documento"))

    def unlink(self):
        move_lines = self.env["hr.employee.movement.line"]
        # Filtrar los registros que no están en estado 'draft' al inicio
        if any(brw_each.state != 'draft' for brw_each in self):
            raise ValidationError(_("No puedes borrar un registro que no sea preliminar"))
        # Mapeo de las líneas de entrada en una sola operación
        inputs = self.mapped('slip_ids.input_line_ids')
        if inputs:
            move_lines += inputs.mapped('movement_id')
        # Llamar al metodo unlink del superclase
        values = super(HrPayslipRun, self).unlink()
        # Calcular total solo si hay líneas de movimiento
        if move_lines:
            move_lines._compute_total()
        return values

    def compute_sheets(self):
        for brw_each in self:
            if brw_each.state != "draft":
                raise ValidationError(_("Solo puedes calcular un rol en estado 'preliminar' "))
            if brw_each.slip_ids:
                for brw_slip in brw_each.slip_ids:
                    brw_slip.compute_sheet()

        return True

    @api.model
    def validate_global_variables(self,year):
        srch=self.env["th.legal.wages"].sudo().search([('name','=',year),('state','=',True)])
        if not srch:
            raise ValidationError(_("Debes definir un salario basico para el año %s") % (year,))

    def validate_payslips(self):
        for brw_each in self:
            if brw_each.slip_ids:
                for brw_slip in brw_each.slip_ids:
                    brw_slip.validate_payslip()
        return True

    def action_verify(self):
        for brw_each in self:
            brw_each.validate_slips()
            for brw_payslip in brw_each.slip_ids:
                brw_payslip.action_verify()
            brw_each.write({"state":"verify"})
            brw_each.calculate_moves()
        return True

    def restore_movements(self):
        for brw_each in self:
            if brw_each.state!='draft':
                raise ValidationError(_("Esta acción solo puede ser ejecutada en un documento en 'borrador'"))
            if brw_each.slip_ids:
                for brw_slip in brw_each.slip_ids:
                    brw_slip.restore_movements()
        return True


    def validate_slips(self):
        OBJ_EMPLOYEE=self.env["hr.employee"].sudo()
        for brw_each in self:
            self._cr.execute("""SELECT
                HP.EMPLOYEE_ID,COUNT(1)
            FROM HR_PAYSLIP_RUN HPR
            INNER JOIN HR_PAYSLIP HP ON HP.PAYSLIP_RUN_ID=HPR.ID
            INNER JOIN HR_CONTRACT HC ON HC.ID=HP.CONTRACT_ID
            WHERE HPR.ID=%s
            GROUP BY HP.EMPLOYEE_ID
            HAVING COUNT(1)>1 """, (brw_each.id,))
            result = self._cr.fetchall()
            if len(result) > 1:
                brw_employee = OBJ_EMPLOYEE.browse(result[0][0])
                raise ValidationError(
                    _("Solo puede existir una registro por empleado %s,%s veces en este documento") % (
                    brw_employee.name, result[0][1]))
            ###se valida documentos por reglas en el mismo mes
            self._cr.execute("""SELECT
                HP.EMPLOYEE_ID,COUNT(1)
            FROM HR_PAYSLIP_RUN HPR
            INNER JOIN HR_PAYSLIP HP ON HP.PAYSLIP_RUN_ID=HPR.ID
            INNER JOIN HR_CONTRACT HC ON HC.ID=HP.CONTRACT_ID
            WHERE HP.COMPANY_ID=%s AND HP.MONTH_ID=%s AND HP.YEAR=%s AND HP.STATE!='cancel' 
            GROUP BY HP.EMPLOYEE_ID
            HAVING COUNT(1)>1""", (brw_each.company_id.id, brw_each.month_id.id, brw_each.year))
            result = self._cr.fetchall()
            if len(result) > 1:
                brw_employee = OBJ_EMPLOYEE.browse(result[0][0])
                raise ValidationError(
                    _("Solo puede existir una registro por empleado %s para %s en el periodo en curso %s del %s.existen %s registros en este periodo.") % (
                        brw_employee.name, brw_each.rule_id.name, brw_each.month_id.name, brw_each.year, result[0][1]))

    def calculate_moves(self):
        for brw_each in self:
            TODAY=fields.Date.context_today(brw_each)
            self._cr.execute("""delete from hr_payslip_move where payslip_run_id=%s;
            insert into hr_payslip_move(
    create_uid,write_uid,create_date,write_date,   payslip_run_id,   payslip_id,  employee_id,rule_id,account_id,debit,credit 
            )          
            select %s as create_uid,
            %s as write_uid,%s as create_date,%s as write_date,
            hpr.id as payslip_run_id,
hp.id as payslip_id,
hp.employee_id,
hpl.salary_rule_id as rule_id,
hsra.account_id,
case when(hsra.account_type='debit') then coalesce(abs(hpl.total),0.00) else 0.00 end::numeric(16,2) as debit,
case when(hsra.account_type='debit') then  0.00 else coalesce(abs(hpl.total),0.00) end::numeric(16,2) as credit
from hr_payslip_run hpr
inner join hr_payslip hp on hp.payslip_run_id=hpr.id
inner join hr_payslip_line hpl on hpl.slip_id=hp.id
inner join hr_salary_rule_account hsra on hsra.rule_id=hpl.salary_rule_id 
	and hsra.company_id=hp.company_id
	and hsra.type='payslip'
where hpr.id=%s;   """,(brw_each.id,self._uid,self._uid,TODAY,TODAY,brw_each.id))