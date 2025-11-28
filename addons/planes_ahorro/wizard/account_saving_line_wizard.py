from odoo import models, fields, api,_
from odoo.exceptions import ValidationError


class AccountSavingLineWizard(models.TransientModel):
    _name = 'account.saving.line.wizard'
    _description = 'Wizard para actualizar fecha en account.saving.line'

    @api.model
    def _get_default_date(self):
        return fields.Date.context_today(self)

    @api.model
    def _get_default_saving_line_ids(self):
        active_ids=self._context.get("active_ids",[])
        if not self._context.get('lock',True):
            active_ids= [(6,0,[])]
        return active_ids

    date = fields.Date(string='Fecha', required=True,default=_get_default_date)
    saving_line_ids=fields.Many2many("account.saving.lines","wizard_account_saving_line_rel","wizard_id","saving_line_id","Linea de Ahorro",default=_get_default_saving_line_ids)
    _rec_name="date"

    def action_invoice(self):
        for brw_each in self:
            if not brw_each.saving_line_ids:
                raise ValidationError(_("Debes seleccionar al menos una cuota para facturar"))
            brw_each.saving_line_ids.action_invoice(date=brw_each.date)  
        return True
