# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api,fields, models,_
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError,UserError

class HrEmployee(models.Model):
    _inherit="hr.employee"

    @api.model
    def _get_selection_marital(self):
        return [
            ('single', 'Soltero(a)'),
            ('married', 'Casado (a)'),
            ('widower', 'Viudo(a)'),
            ('divorced', 'Divorciado(a)'),
            ('free_union', 'Unión libre')
        ]

    @api.model
    def _get_selection_gender(self):
        return [
            ('male', 'Masculino'),
            ('female', 'Femenino')
        ]

    @api.model
    def _get_default_country_id(self):
        brw_user=self.env["res.users"].sudo().browse(self._uid)
        return brw_user.company_id.country_id and brw_user.company_id.country_id.id or False

    previous_day_contract=fields.Integer("Dias Previos Contrato",default=0,tracking=True )
    #tipo_rol = fields.Many2one('tipo.roles', required=False)
    #unidad_administrativa = fields.Many2one('establecimientos', required=False)

    marital = fields.Selection(selection=_get_selection_marital, string='Estado civil', groups=None, default="single",tracking=True)
    gender = fields.Selection(selection=_get_selection_gender, string='Género', groups=None, default="male",tracking=True)

    private_street= fields.Char(related='address_home_id.street', string="Calle privado", groups=None,store=True,readonly=False ,tracking=True)
    private_street2 = fields.Char(related='address_home_id.street2', string="Calle 2 privado", groups=None,store=True,readonly=False,tracking=True)

    private_email = fields.Char(related='address_home_id.email', string="Correo electronico privado", groups=None,store=True,readonly=False,tracking=True)
    phone = fields.Char(related='address_home_id.phone',string="Teléfono privado", groups=None,store=True,readonly=False,tracking=True)

    partner_id = fields.Many2one("res.partner", string="Proveedor", groups=None)

    address_home_id=fields.Many2one("res.partner",compute="_get_compute_address",store=True,readonly=True,groups=None)

    country_id = fields.Many2one("res.country", groups=None,default=_get_default_country_id,tracking=True)
    country_of_birth = fields.Many2one("res.country",  groups=None,default=_get_default_country_id,tracking=True)

    job_id = fields.Many2one("hr.job",  string="Cargo",groups=None)
    ciudad_inicio = fields.Char('Ciudad', required=False)

    tiene_ruc=fields.Boolean(string="Tiene RUC",default=False,tracking=True)

    bank_account_id=fields.Many2one("res.partner.bank","Cuenta Bancaria")

    @api.onchange('first_name','last_name','second_name','mother_last_name')
    def onchange_names(self):
        self.first_name=self.first_name and self.first_name.upper() or ""
        self.last_name = self.last_name and self.last_name.upper() or ""
        self.second_name = self.second_name and self.second_name.upper() or ""
        self.mother_last_name = self.mother_last_name and self.mother_last_name.upper() or ""
        self.name="%s %s %s %s" % ( self.last_name ,self.mother_last_name,self.first_name,self.second_name)

    @api.onchange('partner_id')
    @api.depends('partner_id')
    def _get_compute_address(self):
        for brw_each in self:
            brw_each.address_home_id=brw_each.partner_id

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if args is None:
            args=[]
        if "filter_rule_id" in self._context:
            args = self.filter_by_rule_id(args, self._context.get("filter_date_process", None),
                                            self._context.get("model_name", None),
                                            self._context.get("document_id", False),
                                            self._context.get("filter_rule_id", False),
                                            self._context.get("filter_company_id", False),
                                            self._context.get("filter_legal_iess", False))
        if "filter_type_struct_id" in self._context:
            #structs_by_type=self.env["hr.payroll.structure"].sudo().search([('type_id','=',self._context["filter_type_struct_id"])])
            #structs_ids=structs_by_type.ids+[-1,-1]
            filter_legal_iess = self._context.get("filter_legal_iess", False)

            srch_contract=self.env["hr.contract"].sudo().search([('state', 'in', ('open', )),
             ('company_id', '=', self.env.company.id),
             #('contract_type_id','in',structs_ids),
             ('contract_type_id.legal_iess', '=', filter_legal_iess),
             ])
            employees=srch_contract.mapped('employee_id').ids
            employees+=[-1]
            args+= [('id','in',employees)]
        result = super(HrEmployee, self).name_search(name=name, args=args, operator=operator, limit=limit)
        return result

    @api.model
    def update_data_contracts_employees(self, update_vals):
        update_vals=super(HrEmployee,self).update_data_contracts_employees(update_vals)
        return update_vals

    @api.model
    def _where_calc(self, domain, active_test=True):
        if not domain:
            domain = []
        if "filter_rule_id" in self._context:
            domain = self.filter_by_rule_id(domain, self._context.get("filter_date_process",None),
                                            self._context.get("model_name",None),
                                            self._context.get("document_id",False),
                                            self._context.get("filter_rule_id",False),
                                            self._context.get("filter_company_id",False),
                                            self._context.get("filter_legal_iess", False))
        if "filter_type_struct_id" in self._context:
            # structs_by_type=self.env["hr.payroll.structure"].sudo().search([('type_id','=',self._context["filter_type_struct_id"])])
            # structs_ids=structs_by_type.ids+[-1,-1]
            filter_legal_iess = self._context.get("filter_legal_iess", False)

            srch_contract = self.env["hr.contract"].sudo().search([('state', 'in', ('open',)),
                                                                   ('company_id', '=', self.env.company.id),
                                                                   # ('contract_type_id','in',structs_ids),
                                                                   ('contract_type_id.legal_iess', '=',
                                                                    filter_legal_iess),
                                                                   ])
            employees = srch_contract.mapped('employee_id').ids
            employees += [-1]
            domain+= [('id','in',employees)]
        return super(HrEmployee, self)._where_calc(domain, active_test)

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if domain is None:
            domain = []
        if "filter_rule_id" in self._context:
            domain = self.filter_by_rule_id(domain, self._context.get("filter_date_process",None),
                                            self._context.get("model_name",None),
                                            self._context.get("document_id",False),
                                            self._context.get("filter_rule_id",False),
                                            self._context.get("filter_company_id",False),
                                            self._context.get("filter_legal_iess", False))
        if "filter_type_struct_id" in self._context:
            # structs_by_type=self.env["hr.payroll.structure"].sudo().search([('type_id','=',self._context["filter_type_struct_id"])])
            # structs_ids=structs_by_type.ids+[-1,-1]
            filter_legal_iess = self._context.get("filter_legal_iess", False)

            srch_contract = self.env["hr.contract"].sudo().search([('state', 'in', ('open',)),
                                                                   ('company_id', '=', self.env.company.id),
                                                                   # ('contract_type_id','in',structs_ids),
                                                                   ('contract_type_id.legal_iess', '=',
                                                                    filter_legal_iess),
                                                                   ])
            employees = srch_contract.mapped('employee_id').ids
            employees += [-1]
            domain+= [('id','in',employees)]
        result = super(HrEmployee,self).search_read( domain=domain, fields=fields, offset=offset, limit=limit, order=order)
        return result

    @api.model
    def filter_by_rule_id(self,domain,filter_date_process,model_name,document_id, filter_rule_id,filter_company_id,filter_legal_iess):
        if domain is None:
            domain=[]
        filter_legal_iess = self._context.get("filter_legal_iess", False)

        srch_contract = self.env["hr.contract"].sudo().search([('state', 'in', ('open',)),
                                                               ('company_id', '=', filter_company_id),
                                                               ('contract_type_id.legal_iess', '=', filter_legal_iess),
                                                               ('date_start', '<=',filter_date_process),
                                                               ])
        employees = srch_contract.mapped('employee_id').ids
        employees += [-1]
        domain += [('id', 'in', employees)]
        return domain

    def action_contact_create_validate(self):
        OBJ_PARTNER=self.env["res.partner"]
        OBJ_PARTNER_BANK = self.env["res.partner.bank"]
        for employee in self:
            if not employee.identification_id:
                raise ValidationError(_("Debes definir el # de identificación"))
            partner_vals = {
                'name': employee.name,
                'email': employee.private_email,
                'phone': employee.phone,
                'street': employee.private_street,
                'street2': employee.private_street2,
                'vat': employee.identification_id,
                "company_id":False,
                'l10n_latam_identification_type_id': self.env.ref("l10n_ec.ec_dni").id,
                "company_type": "person",
                # 'is_customer': True,
                # 'is_supplier': True,
                "country_id": employee.country_id and employee.country_id.id or False,
                "function": employee.contract_id and employee.contract_id.job_id.name or employee.job_id.name
            }
            bank_partner_vals = {
                "bank_id": employee.bank_id.id,
                "acc_number": employee.account_number,
                "tipo_cuenta": employee.bank_type == 'checking' and "Corriente" or "Ahorro",
                "currency_id": employee.company_id.currency_id.id,
                "acc_holder_name": employee.name
            }
            partner=employee.work_contact_id
            if partner:
                partner.write(partner_vals)
                #######################
                bank_partner_vals["partner_id"] = partner.id
                brw_partner_bank = OBJ_PARTNER_BANK.search([('partner_id', '=', partner.id),
                                                            ('bank_id', '=', employee.bank_id.id),
                                                            ('acc_number', '=', employee.account_number)
                                                            ])
                if not brw_partner_bank:
                    brw_partner_bank = OBJ_PARTNER_BANK.create(bank_partner_vals)
                else:
                    if len(brw_partner_bank) > 1:
                        raise ValidationError(_("La siguiente combinación de cuentas bancarias %s , # %s") % (
                            employee.bank_id.name, employee.acc_number))
                employee._write({
                    "bank_account_id": brw_partner_bank.id,
                    "partner_id": partner.id
                })
                #self.env.user.notify_info(message='Contacto actualizado correctamente')
            else:
                srch=OBJ_PARTNER.sudo().search([
                    ('vat','=',employee.identification_id)
                ])
                if not srch:
                    try:
                        partner = OBJ_PARTNER.create(partner_vals)
                        bank_partner_vals["partner_id"]=partner.id
                        brw_partner_bank=OBJ_PARTNER_BANK.search([('partner_id','=',partner.id),
                                                                      ('bank_id','=',employee.bank_id.id),
                                                                      ('acc_number','=',employee.account_number)
                                                                      ])
                        if not brw_partner_bank:
                            brw_partner_bank = OBJ_PARTNER_BANK.create(bank_partner_vals)
                        else:
                            if len(brw_partner_bank) > 1:
                                raise ValidationError(_("La siguiente combinación de cuentas bancarias %s , # %s") % (
                                    employee.bank_id.name, employee.acc_number))
                        employee._write({
                            "bank_account_id":brw_partner_bank.id,
                            "partner_id" : partner.id
                        })
                        #self.env.user.notify_info(message='Contacto creado correctamente')
                    except Exception as e:
                        raise ValidationError('Error al crear el contacto:%s' % (str(e),))
                else:
                    if len(srch)==1:
                        partner=srch[0]
                        partner.write(partner_vals)
                        bank_partner_vals["partner_id"] = partner.id
                        brw_partner_bank = OBJ_PARTNER_BANK.search([('partner_id', '=',partner.id),
                                                                    ('bank_id', '=', employee.bank_id.id),
                                                                    ('acc_number', '=', employee.account_number)
                                                                    ])
                        if not brw_partner_bank:
                            brw_partner_bank = OBJ_PARTNER_BANK.create(bank_partner_vals)
                        else:
                            if len(brw_partner_bank)>1:
                                raise ValidationError(_("La siguiente combinación de cuentas bancarias %s , # %s") % (employee.bank_id.name,employee.acc_number))
                        employee._write({
                            "bank_account_id": brw_partner_bank.id,
                            "partner_id": partner.id
                        })
                        #self.env.user.notify_info(message='Contacto actualizado correctamente')
                    else:
                        raise ValidationError('Existen más de un contacto creado con identificación %s ,nombre %s ' % (employee.identification_id,employee.name))
        return True

    @api.onchange('place_of_birth')
    def onchange_place_of_birth(self):
        self.place_of_birth=self.place_of_birth and self.place_of_birth.upper() or None

    @api.onchange('private_street')
    def onchange_private_street(self):
        self.private_street = self.private_street and self.private_street.upper() or None

    @api.onchange('private_street2')
    def onchange_private_street2(self):
        self.private_street2 = self.private_street2 and self.private_street2.upper() or None


    @api.model
    def create(self, vals):
        brw_new = super(HrEmployee, self).create(vals)
        brw_new.action_contact_create_validate()
        return brw_new

    def write(self, vals):
        values= super(HrEmployee, self).write(vals)
        for brw_each in self:
            brw_each.action_contact_create_validate()
        return values

    @api.constrains('identification_id')
    def validate_identification(self):
        for brw_each in self:
            if brw_each.identification_id:
                srch_identification = self.search(
                    [('id', '!=', brw_each.id), ('identification_id', '=', brw_each.identification_id)])
                if len(srch_identification) > 0:
                    raise ValidationError(
                        _("Existe un empleado con la identificación %s ya registrada") % (brw_each.identification_id,))

    def _inverse_work_contact_details(self):
        for employee in self:
            if not employee.work_contact_id:
                srch=self.env['res.partner'].sudo().search([('vat','=',employee.identification_id)])
                if srch:
                    employee.work_contact_id=srch and srch[0].id or False
                else:
                    super(HrEmployee,employee)._inverse_work_contact_details()

