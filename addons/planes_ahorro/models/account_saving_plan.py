# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AccountSavingPlan(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'account.saving.plan'
    _description = 'Plantilla de Planes de ahorro'

    @api.model
    def _get_default_journal_id(self):
        srch=self.env["account.journal"].sudo().search([('type','=','sale')])
        return srch and srch[0].id or False

    @api.model
    def _get_default_document_type_id(self):
        srch = self.env["l10n_latam.document.type"].sudo().search([('code', '=', '01')])
        return srch and srch[0].id or False

    saving_type = fields.Selection([
        ('normal', 'normal'),
        ('ballon', 'Balón'),
    ], string='Tipo de ahorro', default='normal')
    name = fields.Integer(string='Nombre', required=True)
    periods = fields.Integer(string='Periodo',default=0)
    saving_amount    = fields.Monetary(string='Monto de ahorro')

    company_id = fields.Many2one(
        "res.company",
        string="Compañia",
        required=True,
        copy=False,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(related="company_id.currency_id",string='Moneda')

    journal_id = fields.Many2one('account.journal', string='Diario',default=_get_default_journal_id)

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('posted', 'Publicado'),
        ('cancel', 'Cancelado'),
    ], string='Estado', default='draft')

    document_type_id = fields.Many2one('l10n_latam.document.type', string='Tipo de Documento',default=_get_default_document_type_id)

    fixed_amount = fields.Monetary(string='Cantidad Fija')
    quota_amount = fields.Monetary(string='Importe de la cuota')

    rate_inscription = fields.Float(string='Tasa de Inscripción')
    rate_expense = fields.Float(string='Tasa de gastos')
    rate_insurance = fields.Float(string='Tasa de seguro')
    rate_decrement_year = fields.Float(string='Decrecimiento de Tasa')

    @api.model
    def _get_default_inscripcion_id(self):
        return self.env.company.inscripcion_id and self.env.company.inscripcion_id.id or False

    @api.model
    def _get_default_product_id(self):
        return self.env.company.product_id and self.env.company.product_id.id or False

    @api.model
    def _get_default_inscripcion_id(self):
        return self.env.company.inscripcion_id and self.env.company.inscripcion_id.id or False

    @api.model
    def _get_default_seguro_id(self):
        return self.env.company.seguro_id and self.env.company.seguro_id.id or False

    @api.model
    def _get_default_ahorro_account_id(self):
        return self.env.company.ahorro_account_id and self.env.company.ahorro_account_id.id or False


    inscripcion_id = fields.Many2one("product.product", "Gasto de Inscripcion",
                                     default=_get_default_inscripcion_id)
    product_id = fields.Many2one("product.product", "Gasto de Producto",
                                 default=_get_default_product_id)
    seguro_id = fields.Many2one("product.product", "Gasto de Seguro", default=_get_default_seguro_id)
    ahorro_account_id = fields.Many2one("account.account", "Cuenta para Ahorros",
                                        default=_get_default_ahorro_account_id)


    old_id=fields.Integer("Antiguo ID")

    _rec_name = "name"
    _order = "id desc"

    _check_company_auto = True

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id:
            self.inscripcion_id = self.company_id.inscripcion_id and self.company_id.inscripcion_id.id or False
            self.product_id = self.company_id.product_id and self.company_id.product_id.id or False
            self.seguro_id = self.company_id.seguro_id and self.company_id.seguro_id.id or False
            self.ahorro_account_id = self.company_id.ahorro_account_id and self.company_id.ahorro_account_id.id or False
        else:
            self.inscripcion_id=False
            self.product_id = False
            self.seguro_id = False
            self.ahorro_account_id = False

    def action_draft(self):
        for brw_each in self:
            brw_each.write({"state":"draft"})
        return True

    def action_posted(self):
        for brw_each in self:
            brw_each.write({"state":"posted"})
        return True

    def action_cancel(self):
        for brw_each in self:
            brw_each.write({"state":"cancel"})
        return True

    def unlink(self):
        for brw_each in self:
            if brw_each.state!='draft':
                raise ValidationError(_("No puedes eliminar un documento que no este en estado preliminar"))
        return super(AccountSavingPlan,self).unlink()



    


    
