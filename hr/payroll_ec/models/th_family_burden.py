from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from ...calendar_days.tools import CalendarManager,DateManager,MonthManager
dtObj = DateManager()

class ThFamilyBurden(models.Model):
    _inherit="th.family.burden"

    @api.depends('birth_date')
    def _get_work_datas(self):
        for brw_each in self:
            age = 0
            if brw_each.birth_date:
                age = dtObj.years(fields.Date.context_today(self),brw_each.birth_date)
            brw_each.age = age

    genero = fields.Selection([
        ('Hombre', 'Hombre'),
        ('Mujer', 'Mujer'),
    ], 'Sexo', default='Hombre')
    age = fields.Integer(string='Edad',compute="_get_work_datas")
    birth_date=fields.Date(groups=None)

    @api.onchange('birth_date')
    def onchange_birth_date(self):
        age = 0
        warning={}
        if self.birth_date is not None and self.birth_date:
            if self.birth_date > fields.Date.context_today(self):
                warning={"title": _("Error"), "message": _(
                    "Fecha de Nacimiento no puede ser mayor  a la fecha actual")}
            age = dtObj.years(fields.Date.context_today(self), self.birth_date)
        self.age=age
        if warning:
            return {"warning":warning}

    @api.onchange('name')
    def onchange_name(self):
        self.name = self.name and self.name.upper() or None

