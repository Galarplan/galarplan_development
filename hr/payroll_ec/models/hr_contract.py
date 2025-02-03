# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api,fields, models,_
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError,UserError

FIRST_FITTEN_PAYMENT_MODE = [('percent', 'Porcentaje'), ('amount', 'Monto')]


class HrContract(models.Model):
    _inherit="hr.contract"

    struct_id=fields.Many2one("hr.payroll.structure","Estructura Salarial",compute="_get_compute_struct_id",store=False,readonly=True)
    structure_type_id = fields.Many2one("hr.payroll.structure.type", "Tipo de Estructura Salarial", compute="_get_compute_struct_id",
                                store=False, readonly=True)
    type_id=fields.Many2one("hr.contract.type",compute="_get_compute_struct_id",store=True,required=False,readonly=True)

    first_fitten_payment_mode = fields.Selection(FIRST_FITTEN_PAYMENT_MODE, string='First Fitten Payment Mode',
                                                 default='percent')

    job_id=fields.Many2one("hr.job",string="Cargo")
    ciudad_inicio = fields.Char('Ciudad', required=False)

    legal_iess = fields.Boolean(string="Para Afiliados", default=False, store=False, readonly=True,
                                related="structure_type_id.legal_iess")


    @api.onchange('contract_type_id')
    @api.depends('contract_type_id')
    def _get_compute_struct_id(self):
        for brw_each in self:
            brw_each.type_id=brw_each.contract_type_id.id
            brw_each.struct_id=brw_each.contract_type_id.struct_id and brw_each.contract_type_id.struct_id.id or False
            brw_each.structure_type_id=brw_each.contract_type_id.struct_id and brw_each.contract_type_id.struct_id.type_id.id or False



    def _generate_work_entries(self, date_start, date_stop, force=False):
        return False

    @api.model
    def get_days_contracts_end(self,employee_id):
        self._cr.execute(""";with variables as (
	select %s::int as employee_id
)

select hc.id,hc.state,hc.date_start,hc.date_end
from 
variables  
inner join hr_contract hc on hc.employee_id=variables.employee_id 
inner join hr_contract_type hct on hct.id=hc.type_id and 
	coalesce(hct.legal_iess,false)=true
where hc.state in ('close') 
order by hc.id asc""",(employee_id,))
        result=self._cr.fetchall()
        days=0
        for contract_id,state,date_start,date_end in result:
            each_result= (date_end - date_start).days + 1
            days+=each_result
        return days

    def get_current_contract_days(self,date_to=None):
        self.ensure_one()
        brw_contract=self
        date_start = fields.Date.from_string(brw_contract.date_start)
        if date_to is None:
            date_to = fields.Date.context_today(self)
        days= (date_to - date_start).days + 1
        return days

