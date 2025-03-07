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
    seller_id = fields.Many2one('res.users', string='Vendedor',tracking=True,default=lambda self: self.env.user )
    start_date = fields.Date(string='Fecha de inicio',default=fields.Date.today(),tracking=True)
    end_date = fields.Date(string='Fecha de fin',required=False,compute="onchange_lines_date",store=True,tracking=True)

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
    line_ids = fields.One2many('account.saving.lines', 'saving_id', string='Detalle')
    quota_ids= fields.One2many('account.saving.lines', 'saving_id', string='Cuotas',compute="_get_compute_quotas")
    inscription_ids = fields.One2many('account.saving.lines', 'saving_id', string='Inscripción', compute="_get_compute_quotas")

    payment_ids=fields.One2many('account.saving.line.payment', 'saving_id', string='Pagos')
    invoice_ids = fields.One2many('account.move', 'saving_id', string='Facturas')

    # pestaña de contrato
    partner_signed_id = fields.Many2one('res.partner', string='Socio firmante')
    partner_signed_date = fields.Date(string='Fecha de firma')

    company_signed_id = fields.Many2one('res.partner', string='Empresa firmante')
    company_signed_date = fields.Date(string='Fecha de firma')
    
    #pestaña de cuentas
    interest_expenses_account_id = fields.Many2one('account.account', string='Cuenta de Tránsito')

    invoice_count=fields.Integer(compute="_compute_documents",store=True,readonly=False,string="# Facturas")
    payments_count = fields.Integer(compute="_compute_documents", store=True, readonly=False, string="# Pagos")
    documents_count = fields.Integer(compute="_compute_documents", store=False, readonly=False, string="# Documentos")
    payment_move_ids = fields.One2many("account.payment",compute="_compute_documents", store=False, readonly=False, string="Pagos")
    all_move_ids = fields.One2many("account.move", compute="_compute_documents", store=False, readonly=False,
                                       string="Documentos")

    por_pagar = fields.Monetary(string='Por Pagar', compute="_compute_documents", store=True, readonly=False,tracking=True)
    pagos = fields.Monetary(string='Pagos', compute="_compute_documents", store=True, readonly=False,tracking=True)
    pendiente = fields.Monetary(string='Pendiente', compute="_compute_documents", store=True, readonly=False,tracking=True)
    periods = fields.Integer(string='Periodo',default=0,tracking=True)
    serv_inscription_amount=fields.Monetary(string='Inscripción',compute="compute_inscription",store=True,readonly=True,tracking=True)

    old_id = fields.Integer("Antiguo ID",tracking=True)
    old_ref_id = fields.Char("Antiguo REF ID", tracking=True)

    historic_payment_ids=fields.One2many("account.saving.payment","saving_id","Historial de Pagos")
    historic_invoice_ids = fields.One2many("account.saving.invoice", "saving_id", "Historial de Facturas")

    is_credit_sale = fields.Boolean(string="Venta a Crédito")
    is_credit_bank = fields.Boolean(string="Venta por financiento banco")
    is_direct = fields.Boolean(string="Venta Por contado")
    is_galarplan = fields.Boolean(string="Venta Clientes Galarplan")

    property_account_receivable_id = fields.Many2one(
        "account.account",
        string="Cuenta por Cobrar Seleccionada",
        compute="_compute_receivable_account",
        store=True,
        help="Cuenta contable seleccionada según el tipo de venta del cliente.",
    )

    @api.depends('is_credit_sale', 'is_credit_bank', 'is_direct', 'is_galarplan', 'partner_id')
    def _compute_receivable_account(self):
        """ Asigna automáticamente la cuenta contable según la opción seleccionada en el cliente (partner_id) """
        for record in self:
            if not record.partner_id:
                record.property_account_receivable_id = False
                continue

            partner = record.partner_id

            if record.is_credit_sale:
                record.property_account_receivable_id = partner.property_account_receivable_credit_id
            elif record.is_credit_bank:
                record.property_account_receivable_id = partner.property_account_financial_bank_id
            elif record.is_direct:
                record.property_account_receivable_id = partner.property_account_direct_funds_id
            elif record.is_galarplan:
                record.property_account_receivable_id = partner.propoerty_account_adjudicated_id
            else:
                record.property_account_receivable_id = False  # Si no hay selección, queda vacío

    @api.onchange('is_credit_sale', 'is_credit_bank', 'is_direct', 'is_galarplan')
    def _onchange_sale_type(self):
        """ Asegura que solo una opción esté seleccionada a la vez """
        if self.is_credit_sale:
            self.is_credit_bank = False
            self.is_direct = False
            self.is_galarplan = False
        elif self.is_credit_bank:
            self.is_credit_sale = False
            self.is_direct = False
            self.is_galarplan = False
        elif self.is_direct:
            self.is_credit_sale = False
            self.is_credit_bank = False
            self.is_galarplan = False
        elif self.is_galarplan:
            self.is_credit_sale = False
            self.is_credit_bank = False
            self.is_direct = False

    @api.constrains('is_credit_sale', 'is_credit_bank', 'is_direct', 'is_galarplan')
    def _check_only_one_selected(self):
        """ Validación para asegurar que solo un campo esté marcado """
        for record in self:
            selected_count = sum([record.is_credit_sale, record.is_credit_bank, record.is_direct, record.is_galarplan])
            if selected_count == 0:
                raise ValidationError("Debe seleccionar al menos un tipo de venta.")
            elif selected_count > 1:
                raise ValidationError("Solo puede estar seleccionado un tipo de venta.")

    @api.depends('line_ids')
    @api.onchange('line_ids')
    def _get_compute_quotas(self):
        for brw_each in self:
            quota_ids=brw_each.line_ids.filtered(lambda x: x.number!=0)
            inscription_ids = brw_each.line_ids.filtered(lambda x: x.number == 0)
            brw_each.quota_ids=quota_ids
            brw_each.inscription_ids=inscription_ids

    @api.depends('state', 'line_ids.invoice_id', 'payment_ids', 'payment_ids.payment_id','line_ids.migrated_payment_amount','historic_payment_ids','historic_invoice_ids')
    @api.onchange('state', 'line_ids.invoice_id', 'payment_ids', 'payment_ids.payment_id','line_ids.migrated_payment_amount','historic_payment_ids','historic_invoice_ids')
    def _compute_documents(self):
        for brw_each in self:
            invoice_count = 0
            por_pagar,pagos,pendiente=0.00,0.00,0.00
            all_moves=self.env["account.move"].sudo()
            reconciled_moves=self.env["account.move"].sudo()
            other_payments=self.env["account.payment"].sudo()
            if brw_each.state not in ('draft','cancel'):
                account_moves = brw_each.line_ids.mapped('invoice_id').filtered(lambda x: x.state != 'cancel')
                invoice_count=len(account_moves)
                invoice_count+= len(brw_each.historic_invoice_ids.filtered(lambda x: x.invoice_state != 'cancel'))
                ############facturas+asientos
                account_moves += brw_each.line_ids.mapped('plan_ahorro_move_id').filtered(lambda x: x.state != 'cancel')

                reconciled_move_lines = account_moves.mapped('line_ids')
                if reconciled_move_lines:
                    reconciliations = self.env['account.partial.reconcile'].search(['|',
                        ('debit_move_id', 'in', reconciled_move_lines.ids),  # Buscar por la línea de débito
                        ('credit_move_id', 'in', reconciled_move_lines.ids)  # Buscar por la línea de crédito
                    ])
                    reconciled_moves=reconciliations.mapped('debit_move_id').mapped('move_id').filtered(lambda x: not x.payment_id)
                    reconciled_moves+= reconciliations.mapped('credit_move_id').mapped('move_id').filtered(
                        lambda x: not x.payment_id)
                    ###
                    other_payments = reconciliations.mapped('debit_move_id').mapped('move_id').filtered(
                        lambda x: x.payment_id).mapped('payment_id')
                    other_payments += reconciliations.mapped('credit_move_id').mapped('move_id').filtered(
                        lambda x: x.payment_id).mapped('payment_id')
                all_moves=reconciled_moves|account_moves
            for brw_line in brw_each.line_ids:
                por_pagar+=brw_line.por_pagar
                pagos += brw_line.pagos
                pendiente += brw_line.pendiente
            brw_each.invoice_count = invoice_count

            payment_move_ids=brw_each.payment_ids.mapped('payment_id').filtered(lambda x: x.state!='cancel')
            payment_move_ids = payment_move_ids | other_payments
            payments_count=len(payment_move_ids)
            payments_count+=len(brw_each.historic_payment_ids.filtered(lambda x: x.payment_state != 'cancel'))

            brw_each.documents_count=len(all_moves)
            brw_each.all_move_ids=all_moves
            brw_each.payments_count = payments_count
            brw_each.payment_move_ids=payment_move_ids
            brw_each.por_pagar = por_pagar
            brw_each.pagos = pagos
            brw_each.pendiente = pendiente

    _rec_name = "name"
    _order = "id desc"

    def validate_reverse(self):
        for brw_each in self:
            lines = brw_each.line_ids.mapped('invoice_id').filtered(lambda x: x.state in ('draft', 'posted'))
            if lines:
                raise ValidationError(_("No puedes cambiar a borrador si existen facturas publicadas"))
            payments = brw_each.payment_ids.mapped('payment_id').filtered(lambda x: x.state != 'cancel')
            if payments:
                raise ValidationError(_("No puedes cambiar a borrador si existen pagos publicados"))
        return True

    def action_draft(self):
        for brw_each in self:
            brw_each.validate_reverse()
            brw_each.write({"state":"draft"})
        return True

    def validate(self):
        for brw_each in self:
            if not brw_each.line_ids:
                raise ValidationError(_("Al menos una linea debe ser definida"))
            if not (brw_each.is_credit_sale or brw_each.is_credit_bank or brw_each.is_direct or brw_each.is_galarplan):
                raise ValidationError(_("Debes seleccionar al menos un tipo de Venta"))
            if not brw_each.property_account_receivable_id:
                brw_each._compute_receivable_account()
            if not brw_each.property_account_receivable_id:
                raise ValidationError(_("Debes definir la cuenta contable correspondiente") )
            if not self._context.get('pass_validate', False):
                if not brw_each.partner_id.vat:
                    raise ValidationError(_("Debes definir una identificacion al cliente"))
                if not brw_each.partner_id.country_id:
                    raise ValidationError(_("Debes definir un pais para el cliente"))
        return True

    def action_open(self):
        for brw_each in self:
            if not brw_each.line_ids:
                brw_each.compute_lines()
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
            brw_each.validate_reverse()
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
        self.line_ids=[(5,)]
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
            self.journal_id=brw_plan.journal_id and brw_plan.journal_id.id or self._get_default_journal_id()
            self.document_type_id = brw_plan.document_type_id

    @api.onchange('periods','start_date','quota_amount','saving_plan_id','partner_id')
    def onchange_periods(self):
        self.end_date=None
        self.line_ids=[(5,)]
        #self.compute_lines()

    @api.onchange('periods', 'start_date','line_ids','line_ids.date','partner_id')
    @api.depends('periods', 'start_date', 'line_ids', 'line_ids.date','partner_id')
    def onchange_lines_date(self):
        if self.line_ids:
            max_date=None
            dates=self.line_ids.filtered(lambda x: x.date is not None and x.date).mapped('date')
            if dates:
                max_date= max(dates)
            self.end_date =max_date
        else:
            self.end_date = None

    @api.onchange('saving_plan_id','saving_amount')
    @api.depends('saving_plan_id', 'saving_amount')
    def compute_inscription(self):
        DEC=2
        for brw_each in self:
            serv_inscription_amount=0.00
            if brw_each.saving_plan_id:
                serv_inscription_amount = round(
                brw_each.saving_amount * brw_each.saving_plan_id.rate_inscription / 100.00, DEC)
            brw_each.serv_inscription_amount=serv_inscription_amount

    def compute_lines(self):
        DEC=2
        for brw_each in self:
            new_date_process = brw_each.start_date
            total = 0.00
            totalglobal = 0.00
            principal_amount = brw_each.periods!=0 and round(brw_each.saving_amount/brw_each.periods,DEC) or 0.00
            line_ids = [(5,)]
            ###inscripcion
            values = {
                "sequence": 0,
                "number": 0,
                "date": brw_each.start_date,
                "pagos": 0.00,
                "pendiente": 0.00,
                "estado_pago": "sin_aplicar",
                "parent_saving_state": "draft",
                "enabled_for_invoice": False,
                "migrated": False,
                "migrated_has_invoices": False,
                "migrated_payment_amount": False,
                "serv_inscription_amount": round(
                    brw_each.saving_amount * brw_each.saving_plan_id.rate_inscription / 100.00, DEC),
                "rate_inscription": brw_each.saving_plan_id.rate_inscription,

            }
            line_ids.append((0, 0, values))
            ####
            for each_range in range(0, brw_each.periods):
                quota = each_range +1
                new_date_process_temp =brw_each.start_date+ relativedelta(months=quota)
                datevalue =new_date_process_temp
                total += round(principal_amount, DEC)
                if brw_each.periods == each_range :
                    principal_amount = round(principal_amount + round((brw_each.saving_amount - total), DEC), DEC)

                values = {
                    "sequence":each_range ,
                    "number":quota,
                    "date":datevalue,
                    "pagos":0.00,
                    "pendiente":0.00,
                    "estado_pago":"sin_aplicar",
                    "parent_saving_state":"draft",
                    "enabled_for_invoice":False,
                    "migrated":False,
                    "migrated_has_invoices":False,
                    "migrated_payment_amount":False,
                   "principal_amount": principal_amount,
                   "saving_amount": brw_each.quota_amount,
                   "serv_admin_amount": round(
                            principal_amount * brw_each.saving_plan_id.rate_expense / 100.00, DEC),
                   "seguro_amount": round(principal_amount * brw_each.saving_plan_id.rate_insurance / 100.00,
                                               DEC),

                   "serv_admin_percentage":  brw_each.saving_plan_id.rate_expense,
                   "seguro_percentage": brw_each.saving_plan_id.rate_insurance
                }
                print(values)
                line_ids.append((0, 0, values))
                totalglobal += round(principal_amount, DEC)
                if totalglobal > brw_each.saving_amount:
                    continue
            brw_each.line_ids= line_ids
            brw_each.compute_inscription()

    @api.model
    def create_invoices(self, order, domain, last_days=0,post=False):
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
                    brw_each=brw_each.with_context({"post":post})
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

    def action_open_documents(self):
        self.ensure_one()
        return {
            'name': 'Documentos Contables',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('account.view_out_invoice_tree').id, 'tree'),
                (self.env.ref('account.view_move_form').id, 'form')
            ],
            'domain': [('id', 'in', self.all_move_ids.ids)],
        }

    def action_open_payments(self):
        self.ensure_one()
        return {
            'name': 'Pagos',
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('account.view_account_payment_tree').id, 'tree'),
                (self.env.ref('account.view_account_payment_form').id, 'form')
            ],
            'domain': [('id', 'in', self.payment_move_ids.ids)],
        }


    
