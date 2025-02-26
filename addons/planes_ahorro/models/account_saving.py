# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

from datetime import timedelta
from odoo import fields

class AccountSaving(models.Model):
    _inherit="account.saving.plan"
    _name = 'account.saving'
    _description = 'Planes de ahorro'

    @api.model
    def _get_default_name(self):
        brw_ref=self.env.ref("planes_ahorro.seq_plan_ahorro")
        return brw_ref.next_by_id()

    name = fields.Char(string='Nombre', required=True,default=_get_default_name,tracking=True)
    saving_plan_id = fields.Many2one('account.saving.plan',string='Planes de Ahorro	',tracking=True)
    partner_id = fields.Many2one('res.partner', string='Socio',required=True,tracking=True)
    seller_id = fields.Many2one('res.users', string='Vendedor',tracking=True)
    start_date = fields.Date(string='Fecha de inicio',default=fields.Date.today(),tracking=True)
    end_date = fields.Date(string='Fecha de fin',compute="onchange_lines_date",store=True,tracking=True)

    analytic_account_id = fields.Many2one('account.analytic.account', string='Cuenta analítica',tracking=True)

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('open', 'Abierto'),
        ('close', 'Cerrado'),
        ('cancel', 'Anulado')
    ], string='Estado', default='draft',tracking=True)

    state_plan = fields.Selection([
        ('draft', 'Borrador'),
        ('posted', 'Publicado'),
        ('active', 'Activo'),
        ('adjudicated_with_assets', 'Adjudicado con Bien'),
        ('adjudicated_without_assets', 'Adjudicado sin Bien'),
        ('awarded', 'Adjudicado'),
        ('pending_authorizated', 'Autorización de Retiro Pendiente'),
        ('anulled', 'Anulado'),
        ('disabled', 'Desactivado'),
        ('retired', 'Retirado'),
        ('cancelled', 'Cancelado'),
        ('closed', 'Cerrado'),
    ], string='Estado del Plan', default='draft',tracking=True)


    info_migrate = fields.Boolean(string='Información Migrada', default=False)

    #pestaña de cuotas

    line_ids = fields.One2many('account.saving.lines', 'saving_id', string='Cuotas')
    payment_ids=fields.One2many('account.saving.line.payment', 'saving_id', string='Pagos')

    # pestaña de contrato
    partner_signed_id = fields.Many2one('res.partner', string='Socio firmante')
    partner_signed_date = fields.Date(string='Fecha de firma')

    company_signed_id = fields.Many2one('res.partner', string='Empresa firmante')
    company_signed_date = fields.Date(string='Fecha de firma')
    
    #pestaña de cuentas
    interest_expenses_account_id = fields.Many2one('account.account', string='Cuenta de Tránsito')

    invoice_count=fields.Integer(compute="_compute_documents",store=True,readonly=False,string="# Documentos")
    payments_count = fields.Integer(compute="_compute_documents", store=True, readonly=False, string="# Pagos")

    por_pagar = fields.Monetary(string='Por Pagar', compute="_compute_documents", store=True, readonly=False,tracking=True)
    pagos = fields.Monetary(string='Pagos', compute="_compute_documents", store=True, readonly=False,tracking=True)
    pendiente = fields.Monetary(string='Pendiente', compute="_compute_documents", store=True, readonly=False,tracking=True)
    periods = fields.Integer(string='Periodo',default=0,tracking=True)

    old_id = fields.Integer("Antiguo ID",tracking=True)
    old_ref_id = fields.Char("Antiguo REF ID", tracking=True)

    historic_payment_ids=fields.One2many("account.saving.payment","saving_id","Historial de Pagos")

    @api.depends('state', 'line_ids.invoice_id', 'payment_ids', 'payment_ids','line_ids.migrated_payment_amount')
    @api.onchange('state', 'line_ids.invoice_id', 'payment_ids', 'payment_ids','line_ids.migrated_payment_amount')
    def _compute_documents(self):
        for brw_each in self:
            invoice_count = 0
            por_pagar,pagos,pendiente=0.00,0.00,0.00
            if brw_each.state not in ('draft','cancel'):
                invoice_count=len(brw_each.line_ids.mapped('invoice_id').filtered(lambda x: x.state!='cancel'))
            for brw_line in brw_each.line_ids:
                por_pagar+=brw_line.por_pagar
                pagos += brw_line.pagos
                pendiente += brw_line.pendiente
            brw_each.invoice_count = invoice_count
            brw_each.payments_count = len(brw_each.payment_ids)
            brw_each.por_pagar = por_pagar
            brw_each.pagos = pagos
            brw_each.pendiente = pendiente

    _rec_name = "name"
    _order = "id desc"

    def action_draft(self):
        for brw_each in self:
            brw_each.write({"state":"draft"})
        return True

    def validate(self):
        for brw_each in self:
            if not self._context.get('pass_validate', False):
                if not brw_each.partner_id.vat:
                    raise ValidationError(_("Debes definir una identificacion al cliente"))
                if not brw_each.partner_id.country_id:
                    raise ValidationError(_("Debes definir un pais para el cliente"))
        return True

    def action_open(self):
        for brw_each in self:
            brw_each.validate()
            brw_each.write({"state":"open"})
        return True

    def action_close(self):
        for brw_each in self:
            brw_each.validate()
            brw_each.write({"state":"close"})
        return True

    def action_cancel(self):
        for brw_each in self:
            brw_each.write({"state":"cancel"})
        return True

    _check_company_auto = True

    def unlink(self):
        for brw_each in self:
            if brw_each.state!='draft':
                raise ValidationError(_("No puedes eliminar un documento que no este en estado preliminar"))
        return super(AccountSaving,self).unlink()

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
        self.journal_id=False
        brw_plan=self.saving_plan_id
        if brw_plan:
            self.saving_amount =brw_plan.saving_amount or 0.00
            self.fixed_amount = brw_plan.fixed_amount or 0.00
            self.quota_amount =brw_plan.quota_amount or 0.00
            self.rate_inscription = brw_plan.rate_inscription or 0.00
            self.rate_expense = brw_plan.rate_expense or 0.00
            self.rate_insurance = brw_plan.rate_insurance or 0.00
            self.rate_decrement_year =brw_plan.rate_decrement_year or 0.00
            self.periods=int(brw_plan.periods) or 0
            self.journal_id=brw_plan.journal_id
            self.document_type_id = brw_plan.document_type_id

    @api.onchange('periods','start_date')
    def onchange_periods(self):
        self.end_date=None
        self.compute_lines()

    @api.onchange('periods', 'start_date','line_ids','line_ids.date')
    @api.depends('periods', 'start_date', 'line_ids', 'line_ids.date')
    def onchange_lines_date(self):
        if self.line_ids:
            self.end_date = max(self.line_ids.mapped('date')) if self.line_ids.mapped('date') else None
        else:
            self.end_date = None

    def compute_lines(self):
        DEC=2
        for brw_each in self:
            new_date_process = brw_each.start_date
            total = 0.00
            totalglobal = 0.00
            principal_amount = brw_each.periods!=0 and round(brw_each.saving_amount/brw_each.periods,DEC) or 0.00
            line_ids = [(5,)]
            for each_range in range(0, brw_each.periods+1):
                quota = each_range + 1
                new_date_process_temp = new_date_process
                if each_range > 0:
                    new_date_process_temp =brw_each.start_date+ relativedelta(months=each_range)
                datevalue =new_date_process_temp
                total += round(principal_amount, DEC)
                if brw_each.periods == each_range :
                    principal_amount = round(principal_amount + round((brw_each.saving_amount - total), DEC), DEC)

                values = {
                    "sequence":quota,
                    "number":each_range,
                    "date":datevalue,

                    "pagos":0.00,
                    "pendiente":0.00,
                    "estado_pago":"sin_aplicar",
                    "parent_saving_state":"draft",
                    "enabled_for_invoice":False,
                    "migrated":False,
                    "migrated_has_invoices":False,
                    "migrated_payment_amount":False

                }
                if quota>1:
                    values.update({
                        "principal_amount": principal_amount,
                        "saving_amount": brw_each.quota_amount,
                        "serv_admin_amount": round(
                            brw_each.quota_amount * brw_each.saving_plan_id.rate_expense / 100.00, DEC),
                        "seguro_amount": round(brw_each.quota_amount * brw_each.saving_plan_id.rate_insurance / 100.00,
                                               DEC),

                        "serv_admin_percentage":  brw_each.saving_plan_id.rate_expense,
                        "seguro_percentage": brw_each.saving_plan_id.rate_insurance
                    })
                else:
                    values.update({
                        "serv_admin_amount": round(
                            brw_each.saving_amount * brw_each.saving_plan_id.rate_inscription / 100.00, DEC),
                        "serv_admin_percentage":brw_each.saving_plan_id.rate_inscription
                    })
                line_ids.append((0, 0, values))
                totalglobal += round(principal_amount, DEC)
                if totalglobal > brw_each.saving_amount:
                    continue
            brw_each.line_ids= line_ids
        return True

    @api.model
    def create_invoices(self, order, domain, last_days=0):
        TODAY=fields.Date.context_today(self)
        date_from=TODAY - timedelta(days=last_days)
        new_domain = domain + [('saving_id.state','=','open'),
                               ('saving_id.journal_id','!=',False),
                               ('date','>=',date_from),
                               ('date', '<=',TODAY),
                               ('invoice_id','=',False),
                               ('migrated_has_invoices', '!=', True)
                               ]#  # se omite error
        srch = self.env["account.saving.lines"].sudo().search(new_domain, order=order)
        if srch:
            try:
                for brw_each in srch:
                    brw_each.action_invoice()
                    #self._cr.commit()
            except Exception as e:
                result = (str(e))

    def action_open_lines(self):
        self.ensure_one()
        return {
            'name': 'Detalles de Ahorro',
            'type': 'ir.actions.act_window',
            'res_model': 'account.saving.lines',
            'view_mode': 'tree',
            'view_id': self.env.ref('planes_ahorro.account_saving_lines_tree_editable_view').id,
            'domain': [('id', 'in', self.line_ids.ids)],
        }



    
