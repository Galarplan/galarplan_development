# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _


class AccountSaving(models.Model):
    _inherit = 'account.saving.plan'
    _name = 'account.saving'
    _description = 'Planes de ahorro'

    name = fields.Char(string='Nombre', default='Nuevo Plan',required=True)
    saving_plan_id = fields.Many2one('account.saving.plan',string='Planes de Ahorro	')
    partner_id = fields.Many2one('res.partner', string='Socio',required=True)
    seller_id = fields.Many2one('res.users', string='Vendedor')
    start_date = fields.Date(string='Fecha de inicio',default=fields.Date.today())
    end_date = fields.Date(string='Fecha de fin')

    analytic_account_id = fields.Many2one('account.analytic.account', string='Cuenta analítica')

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('open', 'Abierto'),
        ('close', 'Cerrado'),
        ('cancel', 'Cancelado'),
    ], string='Estado', default='draft')
    info_migrate = fields.Boolean(string='Información Migrada', default=False)

    #pestaña de cuotas

    line_ids = fields.One2many('account.saving.lines', 'saving_id', string='Cuotas')

    # pestaña de contrato
    partner_signed_id = fields.Many2one('res.partner', string='Socio firmante')
    partner_signed_date = fields.Date(string='Fecha de firma')

    company_signed_id = fields.Many2one('res.partner', string='Empresa firmante')
    company_signed_date = fields.Date(string='Fecha de firma')
    
    #pestaña de cuentas
    interest_expenses_account_id = fields.Many2one('account.account', string='Cuenta de Tránsito')

    _rec_name = "name"
    _order = "id desc"

    _check_company_auto = True

    @api.onchange('saving_type')
    def onchange_saving_type(self):
        self.saving_plan_id=False

    @api.onchange('saving_plan_id')
    def onchange_saving_plan_id(self):
        self.saving_amount=0.00
        self.fixed_amount = 0.00
        self.quota_amount = 0.00
        self.rate_inscription = 0.00
        self.rate_expense = 0.00
        self.rate_insurance    = 0.00
        self.rate_decrement_year = 0.00
        self.periods=0
        self.journal_id=False
        if self.saving_plan_id:
            self.saving_amount =self.saving_plan_id.saving_amount
            self.fixed_amount = self.saving_plan_id.fixed_amount
            self.quota_amount =self.saving_plan_id.quota_amount
            self.rate_inscription = self.saving_plan_id.rate_inscription
            self.rate_expense = self.saving_plan_id.rate_expense
            self.rate_insurance = self.saving_plan_id.rate_insurance
            self.rate_decrement_year =self.saving_plan_id.rate_decrement_year
            self.periods=self.saving_plan_id.periods
            self.journal_id=self.saving_plan_id.journal_id
            self.document_type_id = self.saving_plan_id.document_type_id

    @api.onchange('periods','start_date')
    def onchange_periods(self):
        self.end_date=None
        if self.start_date:
            self.end_date=self.start_date+relativedelta(months=self.periods)
        self.compute_lines()

    def compute_lines(self):
        DEC=2
        for brw_each in self:
            new_date_process = brw_each.start_date
            total = 0.00
            totalglobal = 0.00
            principal_amount = round(brw_each.saving_amount/brw_each.periods,DEC)
            line_ids = [(5,)]
            for each_range in range(0, brw_each.periods):
                quota = each_range + 1
                new_date_process_temp = new_date_process
                if each_range > 0:
                    new_date_process_temp =brw_each.start_date+ relativedelta(months=each_range)
                datevalue =new_date_process_temp
                total += round(principal_amount, DEC)
                if brw_each.periods == each_range + 1:
                    principal_amount = round(principal_amount + round((brw_each.saving_amount - total), DEC), DEC)

                values = {
                    "sequence":each_range,
                    "number":each_range,
                    "date":datevalue,
                    "principal_amount":principal_amount,
                   "saving_amount":brw_each.quota_amount,
                    "pagos":0.00,
                    "pendiente":0.00,
                    "estado_pago":"pendiente"

                }
                line_ids.append((0, 0, values))
                totalglobal += round(principal_amount, DEC)
                if totalglobal > brw_each.saving_amount:
                    continue
            brw_each.line_ids= line_ids

        return True


    


    
