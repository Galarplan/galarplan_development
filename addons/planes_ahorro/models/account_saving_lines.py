# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
import pytz

from odoo import SUPERUSER_ID


class AccountSavingLines(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'account.saving.lines'
    _description = 'listado de cuotas para planes de ahorro'

    name=fields.Char(compute="_compute_name",store=True)
    sequence=fields.Integer("# Secuencia",required=False,default=0)
    saving_id = fields.Many2one('account.saving', string='Plan de ahorro',ondelete="cascade")
    company_id = fields.Many2one(related="saving_id.company_id", string='Compañía', store=True, readonly=True)

    currency_id = fields.Many2one(related="saving_id.currency_id", string='Moneda',store=False,readonly=True)
    partner_id = fields.Many2one(related="saving_id.partner_id", string='Cliente', store=True, readonly=True)
    number = fields.Integer(string='Número de cuota',tracking=True)
    date = fields.Date(string='Fecha de cuota',tracking=True)
    saving_amount = fields.Monetary(string='Aportaciones',tracking=True)
    principal_amount=fields.Monetary(string='Planes de Ahorro',tracking=True)



    serv_admin_percentage = fields.Float(string='% Serv. Adm.',tracking=True)
    seguro_percentage = fields.Float(string='% Seguro',tracking=True)
    rate_inscription = fields.Float(string='% Inscripción', tracking=True)

    serv_inscription_amount = fields.Monetary(string='Inscripción')
    serv_admin_amount = fields.Monetary(string='Serv. Adm.')
    seguro_amount = fields.Monetary(string='Seguro')

    por_pagar = fields.Monetary(string='Por Pagar', compute="_compute_pendientes", store=True, readonly=False,tracking=True)
    pagos = fields.Monetary(string='Pagos',compute="_compute_pendientes",store=True,readonly=False,tracking=True)
    pendiente = fields.Monetary(string='Pendiente',compute="_compute_pendientes",store=True,readonly=False,tracking=True)
    estado_pago = fields.Selection([ ('sin_aplicar', 'Sin Aplicar'),
                                     ('pendiente', 'Pendiente'),
                                     ('pagado', 'Pagado')], string='Estado de pago', default='pendiente',compute="_compute_pendientes",store=True,readonly=False,tracking=True)
    invoice_id=fields.Many2one("account.move",string="# Factura")
    plan_ahorro_move_id = fields.Many2one("account.move", string="# Asiento Plan de Ahorro")

    parent_saving_state=fields.Selection(related="saving_id.state",store=False,readonly=True)

    payment_line_ids=fields.One2many("account.saving.line.payment","saving_line_id","Pagos Parciales")
    payment_ids = fields.One2many("account.payment", "saving_line_id", "Documentos de Pagos")

    old_id = fields.Integer("Antiguo ID",tracking=True)

    migrated=fields.Boolean("Migrado",default=False,tracking=True)
    migrated_has_invoices=fields.Boolean("# Factura",default=False,tracking=True)
    migrated_payment_amount=fields.Float("Monto Pagado Migrado",default=0.00,tracking=True)
    enabled_for_invoice=fields.Boolean(string='Habilitado para Facturar',readonly=False,default=False)

    days_difference = fields.Integer(
        string="Diferencia en días",
        compute="_compute_days_difference",
        store=True,
        search="_search_days_difference"
    )

    old_ref_id = fields.Char("Antiguo REF ID", tracking=True)

    last_payment_date = fields.Date(string="Última Fecha de Pago", compute="_compute_last_payment_date", store=False,readonly=True)

    origin=fields.Selection([('automatic',' Automatico'),
                             ('imported','Importado')
                             ],string="Origen",default="automatic")

    @api.depends('saving_id','payment_ids','payment_ids.state',
                 'payment_ids.amount_residual')
    def _compute_last_payment_date(self):
        if not self:
            return

        self.env.cr.execute("""
                SELECT aslp.saving_line_id, MAX(COALESCE(am.date, asp.payment_date)) AS date
                FROM account_saving_line_payment aslp
                LEFT JOIN account_payment ap ON ap.id = aslp.payment_id  
                LEFT JOIN account_move am ON am.payment_id = ap.id AND am.state = 'posted'
                LEFT JOIN account_saving_payment asp ON asp.id = aslp.old_payment_id  
                    AND asp.payment_state = 'posted'
                WHERE aslp.saving_id IN %s
                    AND (
                        aslp.old_payment_id IS NOT NULL 
                        OR 
                        aslp.payment_id IS NOT NULL
                    )
                GROUP BY aslp.saving_line_id
            """, (tuple(self._origin.mapped('saving_id.id')),))

        results = dict(self.env.cr.fetchall())  # Convierte resultados en un diccionario
        #print(results)
        for record in self:
            #print(record)
            record.last_payment_date = results.get(record.id, None)

    @api.depends('date')
    def _compute_days_difference(self):
        """Calcula la diferencia en días entre date_filtered y date"""
        for record in self:
            date_filtered=fields.Date.context_today(record)
            if record.date and date_filtered:
                record.days_difference = (date_filtered - record.date).days
            else:
                record.days_difference = 0

    def _search_days_difference(self, operator, value):
        """Permite buscar registros según la diferencia en días entre hoy y 'date'"""
        if operator not in ('=', '!=', '>', '>=', '<', '<='):
            return []

        today = fields.Date.context_today(self)
        query = """
     SELECT  id FROM account_saving_lines 
            WHERE (date - DATE %s {} %s
        """.format(operator)

        self.env.cr.execute(query, (today, value))
        ids = [row[0] for row in self.env.cr.fetchall()]
        return [('id', 'in', ids)]

    @api.depends('saving_id','number')
    def _compute_name(self):
        for brw_each in self:
            brw_each.name="Plan %s ,cuota %s" % (brw_each.saving_id.id,brw_each.number)

    #@api.depends('saving_id.state', 'invoice_id' )
    def _compute_facturable(self):
        invoice_days_enable=int(self.env["ir.config_parameter"].get_param('days.invoice.enable', '120'))
        for brw_each in self:
            enabled_for_invoice=False
            if brw_each.saving_id.state in ('open',):
                if brw_each.invoice_id or brw_each.migrated_has_invoices:
                    enabled_for_invoice = False
                else:
                    days=(brw_each.date - fields.Date.context_today(self)).days
                    if days>=0 or days>= invoice_days_enable:
                        enabled_for_invoice=True
            brw_each.enabled_for_invoice = enabled_for_invoice

    @api.depends('saving_id.state','payment_ids','payment_ids.state','payment_line_ids.type','invoice_id','invoice_id.state','invoice_id.payment_state','principal_amount','serv_admin_amount','seguro_amount','payment_line_ids')
    @api.onchange('saving_id.state''payment_ids','payment_ids.state','payment_line_ids.type','invoice_id','invoice_id.state','invoice_id.payment_   state','principal_amount', 'serv_admin_amount', 'seguro_amount','payment_line_ids')
    def _compute_pendientes(self):
        DEC=2
        for brw_each in self:
            estado_pago="sin_aplicar"
            pendiente=0.00
            pagos=0.00
            por_pagar=0.00
            total=round(brw_each.serv_inscription_amount+brw_each.serv_admin_amount+brw_each.seguro_amount+brw_each.principal_amount,DEC)
            if brw_each.saving_id.state in ('open',):
                estado_pago="pendiente"
                por_pagar=total
                if not brw_each.invoice_id or brw_each.invoice_id.state!='posted':
                    if brw_each.payment_line_ids:
                        for brw_line_payment in brw_each.payment_line_ids:
                            #if brw_line_payment.type!='historic':
                            if brw_line_payment.payment_id:
                                if brw_line_payment.payment_id.state=='posted':
                                    pagos+=brw_line_payment.aplicado
                            else:
                                pagos+=brw_line_payment.aplicado
                    #else:##si no tiene pagos registrados se iria por el campo calculado
                    pagos += brw_each.migrated_payment_amount
                else:##si estado es facturado
                    partner_account= brw_each.saving_id.property_account_receivable_id or brw_each.invoice_id.partner_id.property_account_receivable_id
                    total_invoices,total_payment=0.00,0.00
                    for line in brw_each.invoice_id.line_ids:
                        if line.account_id.reconcile and line.account_id == partner_account:
                            total_invoices+=line.debit
                            total_payment += line.amount_residual
                    if brw_each.plan_ahorro_move_id:
                        for line in brw_each.plan_ahorro_move_id.line_ids:
                            if line.account_id.reconcile and line.account_id == partner_account:
                                total_invoices += line.debit
                                total_payment += line.amount_residual
                    pagos=round(total_invoices-total_payment,DEC)
                pendiente=round(por_pagar-pagos,DEC)
            if brw_each.saving_id.state in ('close',):
                estado_pago = "pagado"
                por_pagar=total
                pagos=por_pagar
                pendiente=0.00
            if brw_each.saving_id.state not in ('draft','cancel'):
                if pendiente==0.00:
                    estado_pago="pagado"
            brw_each.estado_pago=estado_pago
            brw_each.por_pagar = por_pagar
            brw_each.pagos = pagos
            brw_each.pendiente = pendiente

    @api.model
    def calculate_base_amount(self, total, taxes):
        from decimal import Decimal, ROUND_HALF_UP
        def round_excel(value):
            return float(Decimal(value).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))
        """
        Calcula la base imponible a partir del total e impuestos.

        :param total: Valor total (con o sin impuestos).
        :param taxes: Registro(s) del modelo account.tax.
        :return: Valor de l a base imponible.
        """
        base_amount = total
        for tax in taxes:
            if tax.price_include:  # Impuesto incluido en el precio
                base_amount = total / (1 + tax.amount / 100.00)
            else:  # Impuesto excluido
                base_amount = total / (1.00 + tax.amount / 100.00)  # Opcional si se requiere separar impuestos
        return round_excel(base_amount)




    def action_invoice(self,date=None):
        local_date=date
        if date is None:
            utc_now = fields.Datetime.context_timestamp(self, fields.Datetime.now())

            # Convertir a la zona horaria local
            local_tz = pytz.timezone("America/Guayaquil")  # Ajusta según tu zona horaria
            local_now = utc_now.astimezone(local_tz)

            # Si solo necesitas la fecha sin la hora
            local_date = local_now.date()
        post=self._context.get("post",True)
        OBJ_MOVE = self.env["account.move"]
        tz='America/Guayaquil'
        for brw_each in self:
            if not brw_each.saving_id.journal_id:
                raise ValidationError(_("Debes configurar un diario para registrar las facturas de venta en %s") % (brw_each.saving_id.name,))
            if brw_each.parent_saving_state!='open':
                raise ValidationError(_("El estado del plan de ahorro no es valido para facturar en %s") % (brw_each.saving_id.name,) )
            if not (brw_each.saving_id.is_credit_sale or brw_each.saving_id.is_credit_bank or brw_each.saving_id.is_direct or brw_each.saving_id.is_galarplan):
                raise ValidationError(_("Debes seleccionar al menos un tipo de Venta para facturar en %s") % (brw_each.saving_id.name,) )
            if not brw_each.saving_id.property_account_receivable_id:
                brw_each.saving_id._compute_receivable_account()
            if not brw_each.saving_id.property_account_receivable_id:
                raise ValidationError(_("Debes definir la cuenta contable correspondiente para facturar en %s") % (brw_each.saving_id.name,) )
            if brw_each.enabled_for_invoice:
                # srch_invoice=self.env["account.move"].sudo().search([('saving_line_id','=',brw_each.id),
                #                                                      ('state','!=','cancel')
                #                                                      ])
                # if not srch_invoice:
                if True:
                    detail_info_ids = [(5,)]
                    if not (brw_each.serv_inscription_amount > 0):
                        detail_info_ids += [(0, 0, {"campo": "Pago",
                                                    "descripcion": "Pago de Cuota %s/%s" % (brw_each.number, brw_each.saving_id.periods)}),
                                            (0, 0, {"campo": "Descripcion",
                                                    "descripcion": "Factura de gastos administrativos"}),
                                            (0, 0, {"campo": "Valor del Ahorro",
                                                    "descripcion": str(brw_each.principal_amount)})
                                            ]
                    else:
                        detail_info_ids += [(0, 0, {"campo": "Descripcion",
                                                    "descripcion": "Factura de Inscripcion"}),
                                            ]



                    vals = {
                        "partner_id": brw_each.saving_id.partner_id.id,
                        "move_type": "out_invoice",
                        "date": local_date,
                        "invoice_date": local_date,
                        "journal_id": brw_each.saving_id.journal_id.id,
                        "company_id": brw_each.saving_id.company_id.id,
                        "currency_id": brw_each.saving_id.company_id.currency_id.id,
                        "saving_line_id": brw_each.id,
                        'saving_id': brw_each.saving_id.id,
                        "l10n_latam_document_type_id": brw_each.saving_id.document_type_id.id,
                        "l10n_latam_use_documents": True,
                        "state": "draft",
                        "l10n_ec_sri_payment_id": self.env.ref("l10n_ec.P1").id,
                        'is_credit_sale': brw_each.saving_id.is_credit_sale,
                        'is_credit_bank': brw_each.saving_id.is_credit_bank,
                        'is_direct': brw_each.saving_id.is_direct,
                        'is_galarplan': brw_each.saving_id.is_galarplan,
                        'details_invoice_line_id': detail_info_ids
                    }
                    invoice_line_ids = [(5,)]
                    sequence = 1
                    if brw_each.seguro_amount>0:
                        service_id=brw_each.saving_id.saving_plan_id.seguro_id
                        if not  service_id:
                            raise ValidationError(_("Debes configurar un servicio para el seguro en %s") % (brw_each.saving_id.name,) )
                        base_seguro=self.calculate_base_amount(brw_each.seguro_amount, service_id.taxes_id)
                        invoice_line_ids.append((0, 0, {
                                "product_id":service_id.id,
                                "name": service_id.name,
                                "quantity": 1,
                                "price_unit": base_seguro,
                                # "analytic_account_id":brw_each.saving_id.analytic_account_id and brw_each.saving_id.analytic_account_id.id or False,
                                "tax_ids": [(6,0,service_id.taxes_id and service_id.taxes_id.ids or [])] ,
                        }))
                    if brw_each.serv_admin_amount>0:
                        if not  brw_each.saving_id.saving_plan_id.product_id:
                            raise ValidationError(_("Debes configurar un servicio para el gasto administrativo  en %s") % (brw_each.saving_id.name,) )
                        service_id=brw_each.saving_id.saving_plan_id.product_id
                        base_serv = self.calculate_base_amount(brw_each.serv_admin_amount, service_id.taxes_id)
                        invoice_line_ids.append((0, 0, {
                            "product_id": service_id.id,
                            "name": service_id.name,
                            "quantity": 1,
                            "price_unit": base_serv,
                            #"analytic_account_id": brw_each.saving_id.analytic_account_id and brw_each.saving_id.analytic_account_id.id or False,
                            "tax_ids": [(6, 0,
                                         service_id.taxes_id and service_id.taxes_id.ids or [])],
                        }))
                    ###
                    if brw_each.serv_inscription_amount > 0:
                        if not brw_each.saving_id.saving_plan_id.inscripcion_id:
                            raise ValidationError(
                                    _("Debes configurar un servicio para la inscripcion  en %s") % (
                                    brw_each.saving_id.name,))
                        service_id = brw_each.saving_id.saving_plan_id.inscripcion_id
                        base_serv = self.calculate_base_amount(brw_each.serv_inscription_amount, service_id.taxes_id)
                        invoice_line_ids.append((0, 0, {
                            "product_id": service_id.id,
                            "name": service_id.name,
                            "quantity": 1,
                            "price_unit": base_serv,
                            # "analytic_account_id": brw_each.saving_id.analytic_account_id and brw_each.saving_id.analytic_account_id.id or False,
                            "tax_ids": [(6, 0,
                                         service_id.taxes_id and service_id.taxes_id.ids or [])],
                        }))
                    ####
                    if brw_each.principal_amount > 0:
                        if not brw_each.saving_id.saving_plan_id.ahorro_account_id:
                            raise ValidationError(
                                    _("Debes configurar una cuenta para el ahorro  en %s") % (
                                    brw_each.saving_id.name,))
                        if not brw_each.saving_id.property_account_receivable_id:
                            raise ValidationError(_("Debes definir una cuenta por cobrar al cliente para el ahorro  en %s") % (
                                    brw_each.saving_id.name,))
                        ahorro_account_id = brw_each.saving_id.saving_plan_id.ahorro_account_id

                        invoice_line_ids+= [#(5,),
                                     (0, 0, {
                                        'display_type':'planes',
                                         "for_planes":True,
                                         "name": "AHORRO PROGRAMADO",
                                         "credit": brw_each.principal_amount,
                                         "date_maturity":local_date,
                                         "date": local_date,
                                         "partner_id": brw_each.saving_id.partner_id.id,
                                         "account_id": ahorro_account_id and ahorro_account_id.id or False}),
                                     (0, 0, {
                                         'display_type': 'planes',
                                         "for_planes": True,
                                         "name": "CUENTA POR COBRAR AHORRO PROGRAMADO",
                                         "debit": brw_each.principal_amount,
                                         "date_maturity": local_date,
                                         "date": local_date,
                                         "partner_id": brw_each.saving_id.partner_id.id,
                                         "account_id": brw_each.saving_id.property_account_receivable_id.id
                                     })]
                        # ahorro_vals = {
                        #     "line_ids":lines_ids,
                        #     "partner_id": brw_each.saving_id.partner_id.id,
                        #     "move_type": "entry",
                        #     "date": brw_each.date,
                        #     "journal_id": brw_each.saving_id.company_id.ahorro_journal_id.id,
                        #     "company_id": brw_each.saving_id.company_id.id,
                        #     "currency_id": brw_each.saving_id.company_id.currency_id.id,
                        #     "saving_line_id": brw_each.id,
                        #     'saving_id': brw_each.saving_id.id,
                        #     "state": "draft",
                        # }
                        # brw_move_doc = OBJ_MOVE.create(ahorro_vals)
                        # vals["plan_ahorro_move_id"]=brw_move_doc.id
                        # brw_each.write({"plan_ahorro_move_id": brw_move_doc.id})
                    ####
                    sequence += 1
                    vals["invoice_line_ids"] = invoice_line_ids
                    brw_process_doc = OBJ_MOVE.create(vals)
                    if post:
                        brw_process_doc.action_post()
                    if post:
                        for brw_payment in brw_each.payment_line_ids:
                            if brw_payment.type!='historic':
                                self.env["account.saving.line.payment"].reconcile_invoice_with_payment(
                                        brw_process_doc.id, brw_payment.payment_id.id)
                                if brw_process_doc.plan_ahorro_move_id:
                                    #####
                                    self.env["account.saving.line.payment"].reconcile_invoice_with_payment(
                                        brw_process_doc.plan_ahorro_move_id.id, brw_payment.payment_id.id)
                        brw_each.write({"invoice_id": brw_process_doc.id,
                                        "plan_ahorro_move_id": brw_process_doc.plan_ahorro_move_id and brw_process_doc.plan_ahorro_move_id.id or False,
                                        'enabled_for_invoice': False
                                        })
                # else:
                #     if len(srch_invoice)==1:
                #         if srch_invoice.state=='draft':
                #             srch_invoice.action_post()
                #             brw_each.write({"invoice_id": srch_invoice.id,
                #                             "plan_ahorro_move_id": srch_invoice.plan_ahorro_move_id and srch_invoice.plan_ahorro_move_id.id or False,
                #                             'enabled_for_invoice':False
                #                             })
                #         else:#posted
                #             brw_each.write({"invoice_id": srch_invoice.id,
                #                             "plan_ahorro_move_id": srch_invoice.plan_ahorro_move_id and srch_invoice.plan_ahorro_move_id.id or False,
                #                             'enabled_for_invoice':False})
            else:
                if self._context.get("raise_error",False):
                    raise ValidationError(_("La cuota %s no esta habilitada para facturar del plan de ahorro %s") % (brw_each.sequence,brw_each.saving_id.name))
            return True

    def action_do_invoices(self):
        if not self:
            return False

        company_id = self.mapped('saving_id').mapped('company_id')  # Extrae todas las compañías en el recordset

        if len(company_id) > 1:
            raise ValidationError("Solo puedes facturar de una sola compañía a la vez %s" % (company_id.name,))

        for record in self:
            if record.invoice_id or record.migrated_has_invoices:  # Si tiene factura, no cumple
                raise ValidationError("Solo puedes facturar una cuota sin facturar .Revisa %s" % (record.name,))
            if record.saving_id.state != 'open':  # Si no está confirmado, no cumple
                raise ValidationError("Solo puedes facturar una cuota en estado abierto.Revisa %s" % (record.name,) )

        action = self.env.ref('planes_ahorro.action_account_saving_line_wizard').read()[0]
        action['context'] = {'active_ids': self.ids}
        return action
