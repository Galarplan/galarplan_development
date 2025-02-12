# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import ValidationError

class HrLeave(models.Model):
    _inherit = "hr.leave"

    company_id = fields.Many2one(
        "res.company",
        string="Compañia",
        required=True,
        copy=False,
        default=lambda self: self.env.company,
    )
    contract_id = fields.Many2one("hr.contract",required=True)

    vacations = fields.Boolean(related="holiday_status_id.vacations",store=False,readonly=True)
    period_line_ids = fields.One2many("hr.vacation.period.line", "request_id", "Resumen)")

    number_days=fields.Integer(string="# Dias",compute="_get_compute_number_days",store=True,readonly=False)

    @api.onchange('holiday_status_id')
    def onchange_val_holiday_status_id(self):
        self.vacations = self.holiday_status_id and self.holiday_status_id.vacations or False

    @api.onchange('request_date_from', 'request_date_to')
    @api.depends('request_date_from', 'request_date_to')
    def _get_compute_number_days(self):
        for brw_each in self:
            number_days=0
            if brw_each.request_date_to>=brw_each.request_date_from:
                number_days=(brw_each.request_date_to-brw_each.request_date_from).days+1
            brw_each.number_days=number_days

    @api.onchange('employee_id','employee_ids','company_id')
    def onchange_by_contract_employee_ids(self):
        contracts = self.env["hr.contract"].sudo().search(
            [('employee_id', '=', self.employee_id and self.employee_id.id or -1),
             ('state', '=', 'open'),
             ('company_id','=',self.company_id.id)
             ])
        self.contract_id=False
        if contracts:
           self.contract_id=contracts and contracts[0].id or False

    @api.onchange('contract_id','request_date_from', 'request_date_to', 'holiday_status_id','employee_id','employee_ids')
    def onchange_type(self):
        period_line_ids=[(5,)]
        if self.holiday_status_id and self.contract_id and self.request_date_from and self.request_date_to:
            if self.holiday_status_id.vacations:
                vacation_period_ids = self.get_vacation_period_ids(self.request_date_from, self.request_date_to,
                                                               self.contract_id and self.contract_id.id or -1,
                                                               self.holiday_status_id and (self.holiday_status_id.vacations and "VACATION" or '' ) or "",
                                                               self.id or 0)
                period_line_ids=self._onchange_request_dates(vacation_period_ids)

        self.period_line_ids=period_line_ids


    @api.model
    def get_vacation_period_ids(self, date_start, date_stop, contract_id, code, request_id=0):
        self._cr.execute(""";WITH VARIABLES AS (
    SELECT 
    %s::DATE AS DATE_START,
    %s::DATE AS DATE_END,
    %s::INT AS CONTRACT_ID,
    %s::INT AS REQUEST_ID 
    ),
    PERIOD_VACATIONS AS (
    SELECT 
    R.ID, 
    ((R.ATTEMPT_DAYS-R.TAKEN_PENDING_MIGRATED_DAYS-R.WEEKEND_DAYS)-COALESCE((SELECT SUM(L.DAYS) FROM HR_VACATION_PERIOD_LINE L WHERE L.REQUEST_ID!=VARIABLES.REQUEST_ID AND L.PERIOD_ID=R.ID),0)) AS PENDING_DAYS,
    R.YEAR_START,
    R.YEAR_END 
    FROM HR_VACATION_PERIOD R
    INNER JOIN VARIABLES ON 1=1
    WHERE R.CONTRACT_ID=VARIABLES.CONTRACT_ID AND R.STATE='confirmed' 
    ) ,
    GROUP_PERIOD_VACATIONS AS ( 
        SELECT PERIOD_VACATIONS.* ,
        COALESCE((SELECT SUM(X.PENDING_DAYS) 
        FROM PERIOD_VACATIONS X WHERE X.YEAR_START<PERIOD_VACATIONS.YEAR_START),0) AS TOTAL_PENDING_START,
        COALESCE((SELECT SUM(X.PENDING_DAYS) 
        FROM PERIOD_VACATIONS X WHERE X.YEAR_END<=PERIOD_VACATIONS.YEAR_END),0) AS TOTAL_PENDING_END
        FROM PERIOD_VACATIONS
    ),
    VACATION_DAYS AS (
    SELECT CAST(GENERATE_SERIES(DATE_START,DATE_END,'1 DAY'::INTERVAL) AS DATE) AS DATE 
    FROM VARIABLES
    ),
    ORDER_VACATION_DAYS AS (
        SELECT ROW_NUMBER() OVER(ORDER BY DATE ASC) AS NUMBER,* FROM  VACATION_DAYS
    ) 

    SELECT G.ID,G.ID
    FROM ORDER_VACATION_DAYS O
    INNER JOIN VARIABLES ON 1=1
    LEFT JOIN GROUP_PERIOD_VACATIONS G ON O.NUMBER>G.TOTAL_PENDING_START AND O.NUMBER<=G.TOTAL_PENDING_END 
    WHERE G.ID IS NOT NULL  
    ORDER BY G.YEAR_START ASC""", (date_start, date_stop, contract_id, request_id))
        result = self._cr.fetchall()
        if not result:
            return []
        return list(dict(result).keys())

    def test_close_periods(self):
        for brw_each in self:
            if brw_each.holiday_status_id.vacations:
                for brw_vacation in brw_each.period_line_ids:
                    brw_vacation.period_id.validate_period()
                    brw_vacation.period_id.test_period()
        return True

    def _onchange_request_dates(self,vacation_period_ids):
        period_line_ids = [(5,)]  # Clear previous lines
        if not vacation_period_ids:
            return period_line_ids
        total_days = (self.request_date_to - self.request_date_from).days + 1
        overlap_start = self.request_date_from
        overlap_end = self.request_date_to
        if overlap_start <= overlap_end:
            remaining_days = total_days  # Start with the total number of days requested
            for period in self.env["hr.vacation.period"].sudo().browse(vacation_period_ids):
                # Calculate the number of days that fall within this period
                days_in_period = (overlap_end - overlap_start).days + 1
                days_to_take = min( period.attempt_pending_days, days_in_period)
                if days_to_take > 0:
                    period_line_ids.append((0, 0, {
                                'period_id': period.id,
                                'days': days_to_take,
                                'num_days': period.attempt_pending_days,
                                'max_day': total_days
                            }))

                            # Reduce the available pending days in this period
                    period.attempt_pending_days -= days_to_take

                            # Reduce the remaining days to allocate
                    remaining_days -= days_to_take

                    # If no remaining days, exit the loop
                    if remaining_days <= 0:
                        break
        return period_line_ids

    def validate_vacations(self):
        for brw_each in self:
            if brw_each.holiday_status_id.vacations:
                vacaciones=sum(brw_each.period_line_ids.mapped('days'))
                if vacaciones!=brw_each.number_days:
                    raise ValidationError(_("Los # dias deben ser iguales a la suma del detalle de cada periodo "))
        return True

    def action_approve(self):
        self.validate_vacations()
        value= super(HrLeave,self).action_approve()
        self.test_close_periods()
        return value