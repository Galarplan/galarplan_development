# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api,fields, models,_
from odoo.exceptions import ValidationError,UserError
from ...calendar_days.tools import CalendarManager,DateManager,MonthManager
from odoo.tools import float_round, date_utils, convert_file, html2plaintext, is_html_empty, format_amount

dtObj = DateManager()

class HrPayslip(models.Model):
    _inherit="hr.payslip"

    currency_id = fields.Many2one(string="Moneda", related="company_id.currency_id", store=False, readonly=True)


    month_id = fields.Many2one("calendar.month", "Mes", required=False,relate="payslip_run_id.month_id",store=True,readonly=True)
    year = fields.Integer("Año", required=False,store=True,readonly=True,related="payslip_run_id.year")

    total_in = fields.Monetary("Ingresos", digits=(16, 2), required=False, default=0.00,store=True, compute="_compute_total")
    total_out = fields.Monetary("Egresos", digits=(16, 2), required=False, default=0.00,store=True, compute="_compute_total")
    total_provision = fields.Monetary("Provisión", digits=(16, 2), required=False, default=0.00,store=True, compute="_compute_total")
    total_payslip = fields.Monetary("Total", digits=(16, 2), required=False, default=0.00,store=True, compute="_compute_total")

    job_id = fields.Many2one("hr.job", string="Cargo", required=False)
    department_id = fields.Many2one("hr.department", string="Departamento", required=False)
    wage = fields.Monetary("Salario", digits=(16, 2), required=False, default=0.00)

    date_start_contract=fields.Date(string="Fecha Inicio de Contrato")
    date_end_contract = fields.Date(string="Fecha Fin de Contrato")

    legal_basic_wages = fields.Monetary(string="Salario Básico Legal", digits=(16, 2), required=False, default=0.00,
                              compute="_compute_payslip_infos",store=True)

    total_worked_days = fields.Integer(string="Dias Trabajados", required=False, default=0.00,
                                     compute="_compute_payslip_infos", store=True)

    bank_account_id = fields.Many2one("res.partner.bank", "Cuenta de Banco", required=False)

    bank_history_id=fields.Many2one("res.bank","Banco")
    bank_acc_number = fields.Char("# Cuenta")
    bank_tipo_cuenta = fields.Selection([('Corriente','Corriente'),
                                          ('Ahorro','Ahorro'),
                                          ('Tarjeta','Tarjeta'),
                                          ('Virtual', 'Virtual')
                                          ],string="Tipo de Cuenta")

    @api.onchange('month_id', 'year','contract_id','worked_days_line_ids')
    @api.depends('month_id','year','contract_id','worked_days_line_ids')
    def _compute_payslip_infos(self):
        for brw_each in self:
            srch_legal = self.env["th.legal.wages"].sudo().search([('name', '=', brw_each.year)])
            legal_basic_wages=0.00
            if srch_legal:
                legal_basic_wages=srch_legal[0].basic_wages
            brw_each.legal_basic_wages=legal_basic_wages
            brw_each.total_worked_days=brw_each.get_total_days()

    @api.onchange('line_ids')
    def onchange_line_ids(self):
        self.update_total()

    @api.depends('line_ids')
    def _compute_total(self):
        for brw_each in self:
            brw_each.update_total()

    def update_total(self):
        DEC = 2
        for brw_each in self:
            total_in, total_out, total_provision, total_payslip = 0.00, 0.00, 0.00, 0.00
            for brw_line in brw_each.line_ids:
                if brw_line.category_id.code=="PRO":
                    total_provision+=brw_line.total
                if brw_line.category_id.code == "IN":
                    total_in += brw_line.total
                if brw_line.category_id.code == "OUT":
                    total_out += abs(brw_line.total)
            total_payslip=total_in-total_out
            brw_each.total_in = round(total_in, DEC)
            brw_each.total_out = round(total_out, DEC)
            brw_each.total_provision = round(total_provision, DEC)
            brw_each.total_payslip = round(total_payslip, DEC)

    @api.depends('line_ids.total')
    def _compute_basic_net(self):
        DEC=2
        for brw_each in self:
            brw_each.basic_wage = round(brw_each.contract_id.wage,DEC)
            net_wage=0.00
            for brw_line in brw_each.line_ids:
                if brw_line.category_id.code == "IN":
                    net_wage += brw_line.total
                if brw_line.category_id.code == "OUT":
                    net_wage += abs(brw_line.total)
            brw_each.net_wage = round(net_wage,DEC)

    @api.model
    def register_movement(self, contract_id, lst, brw_line):
        lst.append((0, 0, {"contract_id": contract_id,
                           "code": brw_line.rule_id.code,
                           "sequence": len(lst) + 1,
                           "name":  brw_line.name,
                           "amount": brw_line.total_pending,#monto por aplicar
                           "original_pending": brw_line.total_pending,#monto por pendiente
                           "original_amount": brw_line.total_to_paid,#monto original
                           "rule_id":brw_line.rule_id.id,
                           "category_id":brw_line.rule_id.category_id.id,
                           "movement_id": brw_line.id,
                           "add_iess": (brw_line.rule_id.category_code == 'IN' and brw_line.rule_id.add_iess or False),
                           "date_process":brw_line.date_process,
                           "quota": brw_line.quota,
                           "force_payslip":brw_line.rule_id.force_payslip,
                           "movement_ref_id": "%s/%s" % (brw_line.process_id.id,brw_line.id),
                           }))
        return lst

    @api.model
    def get_new_inputs(self, contracts, date_from, date_to,struct_id):
        # TODO: We leave date_from and date_to params here for backwards
        # compatibility reasons for the ones who inherit this function
        # in another modules, but they are not used.
        # Will be removed in next versions.
        """
        Inputs computation.
        @returns: Returns a dict with the inputs that are fetched from the salary_structure
        associated rules for the given contracts.
        """
        OBJ_LINE = self.env["hr.employee.movement.line"].sudo()
        res = [(5,)]
        for contract in contracts:
            current_structure = contract.contract_type_id.struct_id
            rule_ids = current_structure.struct_rule_ids and current_structure.struct_rule_ids.ids or []
            rule_ids += [-1, -1]
            line_srch = OBJ_LINE.search(
                [('date_process', '<=', date_to), 
                ('company_id', '=', contract.company_id.id),
                 ('contract_id', '=', contract.id),
                 ('employee_id', '=', contract.employee_id.id),
                 ('total_pending', '>', 0),
                 ('state', '=', 'approved'),
                 ('rule_id','in',rule_ids)
                 ])
            if line_srch:
                for brw_line in  line_srch:
                    self.register_movement(contract.id,res,brw_line)
        return res

    @api.onchange('date_from','date_to','employee_id','contract_id','struct_id')
    def onchange_employee_id(self):
        self.input_line_ids=[(5,)]#liberar movimientos
        self.job_id=self.contract_id and self.contract_id.job_id or False
        self.department_id =self.contract_id and  self.contract_id.department_id or False
        self.wage=self.contract_id and self.contract_id.wage or 0.00
        self.date_start_contract=self.contract_id and self.contract_id.date_start or None
        self.date_end_contract = self.contract_id and self.contract_id.date_end or None
        self.struct_id=self.contract_id.contract_type_id.struct_id and self.contract_id.contract_type_id.struct_id or False
        self._compute_payslip_infos()
        worked_days_line_ids = self.get_new_worked_day_lines(self.contract_id,
                                                             self.date_from,
                                                            self.date_to)

        input_line_ids = self.get_new_inputs(self.contract_id, self.date_from, self.date_to, self.struct_id)
        self.worked_days_line_ids=worked_days_line_ids
        self.input_line_ids = input_line_ids
        ##########
        if self.contract_id:
            self.set_employee_account_info(self, self.employee_id)
        else:
            self.set_employee_account_info(self, self.env["hr.employee"])

    @api.model
    def get_amount_rules(self,brw_payslip_puts,brw_rule):
        amount=self.get_puts_values(brw_payslip_puts,brw_rule)
        if brw_rule.category_id.code=="IN":
            return amount,amount
        if brw_rule.category_id.code=="OUT":
            return amount,-amount
        return amount,amount

    @api.model
    def get_puts_values(self,brw_payslip_puts,brw_rule):
        DEC=2
        amount=0.00
        for brw_line in brw_payslip_puts:
            if brw_line.rule_id==brw_rule:
                amount+=brw_line.amount
        return round(amount,DEC)

    def _get_localdict(self):
        self.ensure_one()
        localdict=super(HrPayslip,self)._get_localdict()
        new_fx=self.env["dynamic.function"].sudo().initialize()
        localdict.update(new_fx[0])
        return localdict

    def get_total_days(self):
        self.ensure_one()
        brw_payslip = self
        total_days = sum(line.number_of_days for line in brw_payslip.worked_days_line_ids)
        return total_days

    def get_total_wage(self):
        self.ensure_one()
        brw_payslip=self
        DEC = 2
        total_days=brw_payslip.total_worked_days
        amount = round(((brw_payslip.wage / 30.00) * total_days), DEC)
        return amount

    def get_other_incomes_iess(self):
        self.ensure_one()
        brw_payslip=self
        DEC = 2
        other_incomes_iess = sum(input.amount  for input in brw_payslip.input_line_ids if input.add_iess and input.rule_id.category_id.code=='IN')
        amount = round(other_incomes_iess, DEC)
        return amount

    def _get_payslip_lines(self):
        line_vals = []
        for payslip in self:
            if not payslip.contract_id:
                raise UserError(_("There's no contract set on payslip %s for %s. Check that there is at least a contract set on the employee form.", payslip.name, payslip.employee_id.name))

            localdict = self.env.context.get('force_payslip_localdict', None)
            if localdict is None:
                localdict = payslip._get_localdict()

            rules_dict = localdict['rules'].dict
            result_rules_dict = localdict['result_rules'].dict

            blacklisted_rule_ids = self.env.context.get('prevent_payslip_computation_line_ids', [])

            result = {}
            for rule in sorted(payslip.struct_id.struct_rule_ids, key=lambda x: x.sequence):
                localdict["brw_payslip"] = payslip
                localdict["brw_rule"] = rule
                if rule.id in blacklisted_rule_ids:
                    continue
                localdict.update({
                    'result': None,
                    'result_qty': 1.0,
                    'result_rate': 100,
                    'result_name': False
                })
                success_rule,amount,amount_factor=rule._new_satisfy_condition(localdict)
                if success_rule:
                    localdict.update({
                        'amount': amount,
                        'amount_factor': amount_factor
                    })
                    amount, qty, rate = rule._new_compute_rule(localdict)
                    #check if there is already a rule computed with that code
                    previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
                    #set/overwrite the amount computed for this rule in the localdict
                    tot_rule = amount * qty * rate / 100.0
                    localdict[rule.code] = tot_rule
                    result_rules_dict[rule.code] = {'total': tot_rule, 'amount': amount, 'quantity': qty}
                    rules_dict[rule.code] = rule
                    # sum the amount for its salary category
                    localdict = rule.category_id._sum_salary_rule_category(localdict, tot_rule - previous_amount)
                    # Retrieve the line name in the employee's lang
                    employee_lang = payslip.employee_id.sudo().address_home_id.lang
                    # This actually has an impact, don't remove this line
                    context = {'lang': employee_lang}
                    rule_name = rule.with_context(lang=employee_lang).name
                    if localdict['result_name']:
                        rule_name = localdict['result_name']
                    elif rule.code in ['BASIC', 'GROSS', 'NET', 'DEDUCTION', 'REIMBURSEMENT']:  # Generated by default_get (no xmlid)
                        if rule.code == 'BASIC':  # Note: Crappy way to code this, but _(foo) is forbidden. Make a method in master to be overridden, using the structure code
                            if rule.name == "Double Holiday Pay":
                                rule_name = _("Double Holiday Pay")
                            if rule.struct_id.name == "CP200: Employees 13th Month":
                                rule_name = _("Prorated end-of-year bonus")
                            else:
                                rule_name = _('Basic Salary')
                        elif rule.code == "GROSS":
                            rule_name = _('Gross')
                        elif rule.code == "DEDUCTION":
                            rule_name = _('Deduction')
                        elif rule.code == "REIMBURSEMENT":
                            rule_name = _('Reimbursement')
                        elif rule.code == 'NET':
                            rule_name = _('Net Salary')
                    else:
                        rule_name = rule.with_context(lang=employee_lang).name
                    result[rule.code] = {
                        'sequence': rule.sequence,
                        'code': rule.code,
                        'name': rule_name,
                        'note': html2plaintext(rule.note) if not is_html_empty(rule.note) else '',
                        'salary_rule_id': rule.id,
                        'contract_id': localdict['contract'].id,
                        'employee_id': localdict['employee'].id,
                        'amount': amount,
                        'quantity': qty,
                        'rate': rate,
                        'slip_id': payslip.id,
                    }
            line_vals += list(result.values())
        return line_vals

    def compute_by_selected_rule(self,brw_rule):
        self.ensure_one()
        DEC=2
        brw_each=self
        amount, amount_factor=self.get_amount_rules(brw_each.input_line_ids, brw_rule)
        result=round(amount,DEC)!=0.00
        return result,amount,amount_factor

    @api.model
    def get_new_worked_day_lines(self, contracts, date_from, date_to):
        res = [(5,)]
        for contract in contracts:
            date_from = contract.date_start  ##fecha de inicio de contrato
            date_to = date_to
            worked_days = self.env["dynamic.function"].sudo().function("compute_worked_days", {}, *[date_from, date_to])

            work_entry_type = self.env.ref('hr_work_entry.work_entry_type_attendance')
            res.append((0,0,{
                        'sequence': work_entry_type.sequence,
                        'work_entry_type_id': work_entry_type.id,
                        'number_of_days': worked_days,
                        'number_of_hours': worked_days*8.00
                    }))
        return res

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        res=[]
        return res

    def compute_sheet(self):
        for brw_each in self:
            # create/overwrite the rule in the temporary results
            super(HrPayslip,brw_each).compute_sheet()
            brw_each.state="draft"
        return True

    def validate_payslip(self):
        for brw_each in self:
            if not brw_each.struct_id:
                raise ValidationError(
                    _("Empleado %s no tiene definido una estructura salarial") % (brw_each.employee_id.name,))
            if not brw_each.contract_id:
                raise ValidationError(
                    _("Empleado %s no tiene definido un contrato") % (brw_each.employee_id.name,))
            if brw_each.contract_id.state != "open":
                raise ValidationError(
                    _("Contrato de empleado %s debe estar 'EN PROCESO' ") % (brw_each.employee_id.name,))
            if brw_each.company_id!=brw_each.employee_id.company_id:
                raise ValidationError(_("Empleado %s debe pertenecer a la misma compañia seleccionada %s") % (brw_each.employee_id.name,brw_each.company_id.name) )
        return True

    def restore_movements(self):
        for brw_each in self:
            if brw_each.state!='draft':
                raise ValidationError(_("Esta acción solo puede ser ejecutada en un documento en 'borrador'"))
            brw_each.onchange_employee_id()
            brw_each.compute_sheet()
            brw_each.validate_payslip()
        return True

    def unlink(self):
        move_lines = self.env["hr.employee.movement.line"]
        # Verificar si algún registro no está en estado 'draft'
        if any(brw_each.state != 'draft' for brw_each in self):
            raise ValidationError(_("No puedes borrar un registro que no sea preliminar"))
        # Mapeo de líneas de entrada en una sola operación
        inputs = self.mapped('input_line_ids.movement_id')
        move_lines += inputs
        # Llamar al metodo unlink del superclase
        values = super(HrPayslip, self).unlink()
        # Calcular total solo si hay líneas de movimiento
        if move_lines:
            move_lines._compute_total()
        return values

    def action_verify(self):
        for brw_each in self:
            brw_each.validate_payslip()
            brw_each.set_employee_account_info(brw_each, brw_each.employee_id)
            brw_each.compute_sheet()
            if brw_each.total_payslip<0.00:
                raise ValidationError(_("No puede existir un rol en negativo.Verificar el rol de %s") % (brw_each.employee_id.name,))
            if not brw_each.bank_account_id:
                raise ValidationError(_("Para confirmar el rol ,debe tener configurado una cuenta bancaria el empledo %s") % (brw_each.employee_id.name,))
            brw_each.write({"state":"verify"})
        return True

    @api.model
    def set_employee_account_info(self,obj,brw_employee):
        def clear_account_info(obj):
            obj.bank_account_id = False
            obj.bank_history_id = False
            obj.bank_acc_number = None
            obj.bank_tipo_cuenta = None
        if not brw_employee:
            clear_account_info(obj)
        else:
            if brw_employee.bank_account_id:
                obj.bank_account_id = brw_employee.bank_account_id.id
                obj.bank_history_id = obj.bank_account_id.bank_id
                obj.bank_acc_number = obj.bank_account_id.acc_number
                obj.bank_tipo_cuenta = obj.bank_account_id.tipo_cuenta
            else:
                clear_account_info(obj)