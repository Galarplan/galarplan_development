# coding: utf-8
from odoo.exceptions import ValidationError
from odoo import api, fields, models, _, SUPERUSER_ID
import base64
from xml.etree.ElementTree import Element, SubElement, tostring
from ...message_dialog.tools import FileManager
from ...calendar_days.tools import DateManager
from ...calendar_days.tools import CalendarManager

fileO = FileManager()
dateO = DateManager()
calendarO = CalendarManager()


class hr_employee_payslip_reports_wizard(models.TransientModel):
    _name = "hr.employee.payslip.reports.wizard"
    _description = "Reportes de Nomina"

    @api.model
    def get_default_year(self):
        return fields.Date.today().year

    @api.model
    def get_default_month_id(self):
        month = fields.Date.today().month
        srch = self.env["calendar.month"].sudo().search([('value', '=', month)])
        return srch and srch[0].id or False

    company_id = fields.Many2one("res.company", "Compañia")

    type_report = fields.Selection([('ATS', '(ATS) ANEXO TRANSACCIONAL SIMPLIFICADO')], default='ATS', copy=False)

    year = fields.Integer("Año", default=get_default_year)
    month_id = fields.Many2one("calendar.month", "Mes", required=True, default=get_default_month_id)

    @api.model
    def get_default_date_start(self):
        if self._context.get("is_report", False):
            NOW = fields.Date.today()
            YEAR = NOW.year
            MONTH = NOW.month
            return dateO.create(YEAR, MONTH, 1).date()
        return None

    @api.model
    def get_default_date_end(self):
        if self._context.get("is_report", False):
            NOW = fields.Date.today()
            YEAR = NOW.year
            MONTH = NOW.month
            LAST_DAY = calendarO.days(YEAR, MONTH)
            return dateO.create(YEAR, MONTH, LAST_DAY).date()
        return None

    @api.model
    def _get_default_type_struct_id(self):
        srch = self.env["hr.payroll.structure.type"].sudo().search([])
        return srch and srch[0].id or False

    date_start = fields.Date("Fecha Inicial", required=True, store=True, readonly=False, default=get_default_date_start)
    date_end = fields.Date("Fecha Final", required=True, store=True, readonly=False, default=get_default_date_end)

    type_struct_id = fields.Many2one("hr.payroll.structure.type", "Tipo", required=False,
                                     default=_get_default_type_struct_id)

    @api.onchange('year', 'month_id')
    def onchange_year_month(self):
        YEAR = self.year
        MONTH = self.month_id.value

        LAST_DAY = calendarO.days(YEAR, MONTH)
        self.date_start = dateO.create(YEAR, MONTH, 1).date()
        self.date_end = dateO.create(YEAR, MONTH, LAST_DAY).date()

    def process_report(self):
        REPORT = self._context.get('default_report', '')
        self = self.with_context({"no_raise": True})
        self = self.with_user(SUPERUSER_ID)
        for brw_each in self:
            try:
                OBJ_REPORT_PAYSLIP=self.env["hr.payslip.run"].sudo()
                context={}
                if REPORT=="gps_hr.report_payslip_runs_report_xlsx_act":

                    domain=[('month_id','=',brw_each.month_id.id),
                                                                ('year','=',brw_each.year),
                                                                ('state','!=','cancelled')
                                                                ]
                    if brw_each.company_id:
                        domain+= [('company_id', '=', brw_each.company_id.id) ]
                    if brw_each.type_struct_id:
                        domain += [('type_struct_id', '=', brw_each.type_struct_id.id)]

                    srch_payslip_run=OBJ_REPORT_PAYSLIP.search(domain)
                    if not srch_payslip_run:
                        raise ValidationError(_("Sin resultados"))
                    context = dict(active_ids=srch_payslip_run.ids,
                                   active_id=srch_payslip_run[0].id,
                                   active_model=OBJ_REPORT_PAYSLIP._name,
                                   landscape=True
                                   )
                    OBJ_REPORT_PAYSLIP = OBJ_REPORT_PAYSLIP.with_context(context)
                report_value = OBJ_REPORT_PAYSLIP.env.ref(REPORT).with_user(SUPERUSER_ID).report_action(OBJ_REPORT_PAYSLIP)
                report_value["target"] = "new"
                return report_value
            except Exception as e:
                raise ValidationError(_("Error al Imprimir %s -- %s") % (REPORT, str(e),))

    # endregion


