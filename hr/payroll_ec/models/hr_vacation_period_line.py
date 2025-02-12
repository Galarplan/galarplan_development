from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from ...calendar_days.tools import CalendarManager, DateManager, MonthManager

dtObj = DateManager()

class HrVacationPeriodLine(models.Model):
    _name = "hr.vacation.period.line"
    _description = "Detalle de Periodo de vacaciones"

    period_id = fields.Many2one("hr.vacation.period", "Periodo de Vacaciones", ondelete="cascade")
    request_id = fields.Many2one("hr.leave", "Solicitud", ondelete="cascade")
    days = fields.Integer("Dia(s)", required=True, default=0)
    num_days = fields.Integer("Dia(s) por Tomar de la Solicitud", required=True, default=0)
    max_day = fields.Integer("Dia Limite dentro de la Solicitud", required=True, default=0)

    date_start = fields.Date(related="request_id.request_date_from", string="Fecha de Inicio", store=True, readonly=True)
    date_stop = fields.Date(related="request_id.request_date_to", string="Fecha de Fin", store=True, readonly=True)
    state = fields.Selection(related="request_id.state",string="Estado", store=True, readonly=True)

    _sql_constraints = [
        ("unique_period_request", "unique(period_id,request_id)", "Periodo de Vacaciones debe ser único por contrato")
    ]

    @api.onchange('period_id')
    def onchange_period_id(self):
        for brw_each in self:
            attempt_pending_days=1
            if brw_each.period_id:
                attempt_pending_days = min(brw_each.period_id.attempt_pending_days,brw_each.request_id.number_of_days)
            brw_each.days=attempt_pending_days

    @api.onchange('days', 'period_id')
    def _onchange_days(self):
        if self.period_id:
            if self.days <= 0:
                raise ValidationError("El número de días debe ser mayor a 0.")
            if self.period_id and self.days > self.period_id.attempt_pending_days:
                raise ValidationError(
                    "El número de días no puede ser mayor que los días pendientes en el período de vacaciones.")


    def unlink(self):
        for brw_each in self:
            if brw_each.period_id.state == "ended":
                raise ValidationError(_("Periodo de Vacaciones %s finalizado") % (brw_each.period_id.name,))
            if brw_each.request_id.state == "ended":
                raise ValidationError(_("Solicitud de Vacaciones %s finalizada") % (brw_each.request_id.full_name,))
        return super(HrVacationPeriodLine, self).unlink()


