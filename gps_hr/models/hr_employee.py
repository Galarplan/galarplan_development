# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api,fields, models,_
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError,UserError

class HrEmployee(models.Model):
    _inherit="hr.employee"

    previous_day_contract=fields.Integer("Dias Previos Contrato",default=0)

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if args is None:
            args=[]
        if "filter_rule_id" in self._context:
            args = self.filter_by_rule_id(args, self._context.get("filter_date_process", None),
                                            self._context.get("model_name", None),
                                            self._context.get("document_id", False),
                                            self._context.get("filter_rule_id", False),
                                            self._context.get("filter_company_id", False))
        if "filter_type_struct_id" in self._context:
            structs_by_type=self.env["hr.payroll.structure"].sudo().search([('type_id','=',self._context["filter_type_struct_id"])])
            structs_ids=structs_by_type.ids+[-1,-1]
            srch_contract=self.env["hr.contract"].sudo().search([('state', 'in', ('open', )),
             ('company_id', '=', self.env.company.id),
             ('contract_type_id','in',structs_ids)
             ])
            employees=srch_contract.mapped('employee_id').ids
            employees+=[-1]
            args+= [('id','in',employees)]
        result = super(HrEmployee, self).name_search(name=name, args=args, operator=operator, limit=limit)
        return result

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if domain is None:
            domain = []
        if "filter_rule_id" in self._context:
            domain = self.filter_by_rule_id(domain, self._context.get("filter_date_process",None),
                                            self._context.get("model_name",None),
                                            self._context.get("document_id",False),
                                            self._context.get("filter_rule_id",False),
                                            self._context.get("filter_company_id",False))
        if "filter_type_struct_id" in self._context:
            structs_by_type=self.env["hr.payroll.structure"].sudo().search([('type_id','=',self._context["filter_type_struct_id"])])
            structs_ids=structs_by_type.ids+[-1,-1]
            srch_contract=self.env["hr.contract"].sudo().search([('state', 'in', ('open', )),
             ('company_id', '=', self.env.company.id),
             ('contract_type_id','in',structs_ids)
             ])
            employees=srch_contract.mapped('employee_id').ids
            employees+=[-1]
            domain+= [('id','in',employees)]
        result = super(HrEmployee,self).search_read( domain=domain, fields=fields, offset=offset, limit=limit, order=order)
        return result

    @api.model
    def filter_by_rule_id(self,domain,filter_date_process,model_name,document_id, filter_rule_id,filter_company_id):
        if domain is None:
            domain=[]
        return domain
