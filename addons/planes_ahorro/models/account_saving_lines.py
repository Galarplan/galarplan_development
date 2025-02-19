# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountSavingLines(models.Model):
    _name = 'account.saving.lines'
    _description = 'listado de cuotas para planes de ahorro'

    name=fields.Char(compute="_compute_name",store=True)
    sequence=fields.Integer("# Secuencia",required=True)
    saving_id = fields.Many2one('account.saving', string='Plan de ahorro',ondelete="cascade")
    currency_id = fields.Many2one(related="saving_id.currency_id", string='Moneda',store=False,readonly=True)
    number = fields.Integer(string='Número de cuota')
    date = fields.Date(string='Fecha de cuota')
    saving_amount = fields.Monetary(string='Aportaciones')
    principal_amount=fields.Monetary(string='Planes de Ahorro')

    serv_admin_percentage = fields.Float(string='% Serv. Adm.')
    seguro_percentage = fields.Float(string='% Seguro')

    serv_admin_amount = fields.Monetary(string='Serv. Adm.')
    seguro_amount = fields.Monetary(string='Seguro')

    por_pagar = fields.Monetary(string='Por Pagar', compute="_compute_pendientes", store=True, readonly=False)
    pagos = fields.Monetary(string='Pagos',compute="_compute_pendientes",store=True,readonly=False)
    pendiente = fields.Monetary(string='Pendiente',compute="_compute_pendientes",store=True,readonly=False)
    estado_pago = fields.Selection([ ('sin_aplicar', 'Sin Aplicar'),
                                     ('pendiente', 'Pendiente'),
                                     ('pagado', 'Pagado')], string='Estado de pago', default='pendiente',compute="_compute_pendientes",store=True,readonly=False)
    invoice_id=fields.Many2one("account.move",string="# Factura")

    parent_saving_state=fields.Selection(related="saving_id.state",store=False,readonly=True)

    payment_line_ids=fields.One2many("account.saving.line.payment","saving_line_id","Pagos Parciales")

    old_id = fields.Integer("Antiguo ID")

    migrated=fields.Boolean("Migrado",default=False)
    migrated_has_invoices=fields.Boolean("# Factura")
    migrated_payment_amount=fields.Monetary("Monto Pagado Migrado",default=0.00)
    enabled_invoice=fields.Boolean(string='Habilitado para Facturar',compute="_compute_facturable",store=False,readonly=False)

    @api.depends('saving_id','number')
    def _compute_name(self):
        for brw_each in self:
            brw_each.name="Plan %s ,cuota %s" % (brw_each.saving_id.id,brw_each.number)

    @api.depends('saving_id.state', 'invoice_id' )
    @api.onchange('saving_id.state', 'invoice_id')
    def _compute_facturable(self):
        invoice_days_enable=int(self.env["ir.config_parameter"].get_param('days.invoice.enable', '120'))
        for brw_each in self:
            enabled_invoice=False
            if brw_each.saving_id.state in ('open',):
                if brw_each.invoice_id or brw_each.migrated_has_invoices:
                    enabled_invoice = False
                else:
                    days=(brw_each.date - fields.Date.context_today(self)).days
                    print(days)
                    enabled_invoice = days>0 or days>= -invoice_days_enable
            brw_each.enabled_invoice = enabled_invoice

    @api.depends('saving_id.state','invoice_id','principal_amount','serv_admin_amount','seguro_amount','payment_line_ids')
    @api.onchange('saving_id.state','invoice_id','principal_amount', 'serv_admin_amount', 'seguro_amount','payment_line_ids')
    def _compute_pendientes(self):
        DEC=2
        for brw_each in self:
            estado_pago="sin_aplicar"
            pendiente=0.00
            pagos=0.00
            por_pagar=0.00
            if brw_each.saving_id.state in ('open',):
                estado_pago="pendiente"
                por_pagar=round(brw_each.serv_admin_amount+brw_each.seguro_amount+brw_each.principal_amount,DEC)
                for brw_line_payment in brw_each.payment_line_ids:
                    pagos+=brw_line_payment.aplicado
                pagos+=brw_each.migrated_payment_amount
                pendiente=round(por_pagar-pagos,DEC)
            if brw_each.saving_id.state in ('close',):
                estado_pago = "pagado"
                por_pagar=round(brw_each.serv_admin_amount+brw_each.seguro_amount+brw_each.principal_amount,DEC)
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
        """
        Calcula la base imponible a partir del total e impuestos.

        :param total: Valor total (con o sin impuestos).
        :param taxes: Registro(s) del modelo account.tax.
        :return: Valor de l a base imponible.
        """
        base_amount = total
        for tax in taxes:
            if tax.price_include:  # Impuesto incluido en el precio
                base_amount = total / (1 + tax.amount / 100)
            else:  # Impuesto excluido
                base_amount = total / (1 + tax.amount / 100)  # Opcional si se requiere separar impuestos
        return base_amount

    def action_invoice(self):
        OBJ_MOVE = self.env["account.move"].sudo()
        for brw_each in self:
            if brw_each.parent_saving_state!='open':
                raise ValidationError(_("El estado del plan de ahorro no es valido para facturar"))
            if not brw_each.invoice_id:
                vals = {
                    "partner_id":brw_each.saving_id.partner_id.id,
                    "move_type":"out_invoice",
                    "date": brw_each.date,
                    "invoice_date":brw_each.date,
                    "journal_id":brw_each.saving_id.journal_id.id,
                    "company_id": brw_each.saving_id.company_id.id,
                    "currency_id": brw_each.saving_id.company_id.currency_id.id,
                    "saving_line_id":brw_each.id,
                    "l10n_latam_document_type_id": brw_each.saving_id.document_type_id.id,
                    "l10n_latam_use_documents": True,
                    "state":"draft",
                    "l10n_ec_sri_payment_id":self.env.ref("l10n_ec.P1").id
                }
                invoice_line_ids = [(5,)]
                sequence = 1
                if brw_each.seguro_amount>0:
                    service_id=brw_each.saving_id.saving_plan_id.seguro_id
                    if not  service_id:
                        raise ValidationError(_("Debes configurar un servicio para el seguro"))
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
                    if brw_each.sequence>1:
                        if not  brw_each.saving_id.saving_plan_id.product_id:
                            raise ValidationError(_("Debes configurar un servicio para el gasto administrativo"))
                        service_id=brw_each.saving_id.saving_plan_id.product_id
                    else:
                        if not  brw_each.saving_id.saving_plan_id.inscripcion_id:
                            raise ValidationError(_("Debes configurar un servicio para la inscripcion"))
                        service_id=brw_each.saving_id.saving_plan_id.inscripcion_id
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
                sequence += 1
                vals["invoice_line_ids"] = invoice_line_ids
                brw_process_doc = OBJ_MOVE.create(vals)
                brw_process_doc.action_post()
                for brw_payment in brw_each.payment_line_ids:
                    self.env["account.saving.line.payment"].reconcile_invoice_with_payment(
                            brw_process_doc.id, brw_payment.payment_id.id)
                brw_each.write({"invoice_id": brw_process_doc.id})
            else:
                if self._context.get("raise_error",False):
                    raise ValidationError(_("La cuota %s ya esta facturada del plan de ahorro %s") % (brw_each.sequence,brw_each.saving_id.id))
        return True