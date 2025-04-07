from odoo import api, fields, models,_
from odoo.exceptions import ValidationError


class AccountSavingPaymentWizard(models.TransientModel):
    _name = 'account.saving.payment.wizard'
    _description = 'Wizard to Create Account Payments'

    @api.model
    def _get_default_saving_id(self):
        return self._context.get("active_ids") and self._context.get("active_ids")[0] or False

    saving_id  =fields.Many2one("account.saving","Plan de Ahorro",default=_get_default_saving_id)
    company_id=fields.Many2one(related='saving_id.company_id',store=False,readonly=True)
    saving_line_ids = fields.Many2many(
        'account.saving.lines',
        string='Lineas de Ahorro',
        domain=[('estado_pago', '=', 'pendiente')],  # Ajusta el dominio según tus necesidades
        required=True,
    )
    payment_date = fields.Date(
        string='Fecha de Pago',
        default=fields.Date.context_today,
        required=True,
    )
    payment_journal_id = fields.Many2one(
        'account.journal',
        string='Diario',
        required=True,
    )
    payment_method_id = fields.Many2one(
        'account.payment.method',
        string='Metodo de Pago',compute="onchange_payment_journal",
        required=True,
    )
    enable_residual=fields.Boolean("Habilitar Saldo",default=False)
    ref=fields.Char("Memo",required=True)

    @api.onchange('payment_journal_id')
    @api.depends('payment_journal_id')
    def onchange_payment_journal(self):
        self.ensure_one()

        # Verifica si se seleccionó un diario
        if self.payment_journal_id:
            # Filtra los métodos de pago asociados al diario para pagos entrantes (inbound)
            payment_methods = self.payment_journal_id.inbound_payment_method_line_ids
            if payment_methods:
                # Establece el primer método de pago disponible como valor por defecto
                self.payment_method_id = payment_methods[0].payment_method_id
            else:
                # Limpia el campo si no hay métodos disponibles
                self.payment_method_id = False
        else:
            # Limpia el campo si no hay un diario seleccionado
            self.payment_method_id = False

    amount = fields.Monetary(
        string='Monto',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    payment_ids=fields.One2many("account.saving.payment.line.wizard","wizard_id","Pagos")
    # @api.depends('saving_line_ids')
    # def _compute_total_amount(self):
    #     for wizard in self:
    #         wizard.amount = sum(wizard.saving_line_ids.mapped('amount'))

    @api.onchange('saving_line_ids', 'amount')
    def onchange_savings(self):
        self.ensure_one()

        # Variables iniciales
        payment_ids = [(5,)]  # Limpia los registros existentes
        acum = 0

        # Iterar sobre las líneas seleccionadas
        for brw_line in self.saving_line_ids:
            pendiente = brw_line.pendiente
            aplicado = min(pendiente,
                           self.amount - acum)  # Aplica solo lo necesario para no exceder el monto disponible

            # Si aún queda saldo disponible para aplicar
            if aplicado > 0:
                payment_ids.append((0, 0, {
                    "number": brw_line.number,
                    "date": brw_line.date,
                    "saving_line_id": brw_line.id,
                    "line_id": brw_line.id,
                    "aplicado": aplicado
                }))
                acum += aplicado  # Acumula el monto aplicado
            if acum >= self.amount:  # Detén el proceso si el monto se ha cubierto completamente
                break

        # Agregar una línea para el excedente, si queda saldo disponible
        sobrante = self.amount - acum
        if sobrante > 0:
            payment_ids.append((0, 0, {
                "aplicado": sobrante,
                "number": 99999999,
            }))

        # Asignar las líneas calculadas
        self.payment_ids = payment_ids

    def action_create_payment(self):
        DEC=2
        """Crea un registro de account.payment basado en las líneas seleccionadas"""
        self.ensure_one()
        if self.amount<=0.00:
            raise ValidationError(_("El valor debe ser mayor a 0"))
        if not self.saving_line_ids:
            raise ValidationError(_("Al menos una cuota debe ser seleccionada"))
        sobrantes=self.payment_ids.filtered(lambda x: x.number>=99999999)
        if sobrantes:
            sobrante=round(sum(sobrantes.mapped('aplicado')),DEC)
            raise ValidationError(_("Todo el monto del pago debe distribuirse completamente en una o más cuotas, sin dejar saldos sobrantes.Sobran %s") % (sobrante,))
        payment_vals = {
            'date': self.payment_date,
            'journal_id': self.payment_journal_id.id,
            'payment_method_id': self.payment_method_id.id,
            'company_id': self.saving_id.company_id.id,
            'amount': self.amount,
            'currency_id': self.currency_id.id,
            'partner_type': 'customer',  # Cambiar según necesidad
            'partner_id': self.saving_id.partner_id.id,  # Podrías vincular a un partner
            'ref': self.ref,
        }
        payment = self.env['account.payment'].create(payment_vals)
        for line in payment.line_ids.filtered(lambda l: l.account_id == payment.partner_id.property_account_receivable_id):
            line.account_id = self.saving_id.property_account_receivable_id  # Usa la cuenta configurada en el cliente

        payment.action_post()
        payment.message_post(
            body='PAGO DE PLAN DE AHORRO %s' % (self.saving_id.id,),
            subject="Nota Automática",
            message_type="notification",
            subtype_xmlid="mail.mt_note"
        )
        lines=[]
        for brw_line in self.payment_ids:
            lines.append((0,0,{
                "number":brw_line.saving_line_id.number,
                "date": brw_line.saving_line_id.date,
                "saving_line_id": brw_line.saving_line_id.id,
                "pendiente":brw_line.saving_line_id.pendiente,
                "aplicado": brw_line.aplicado,
                "payment_id":payment.id,
                "reconciled":False
            }))
            if brw_line.saving_line_id.invoice_id and payment:
                self.env["account.saving.line.payment"].reconcile_invoice_with_payment(brw_line.saving_line_id.invoice_id.id,
                                                                                       payment.id)
                if brw_line.saving_line_id.plan_ahorro_move_id:
                    #####
                    self.env["account.saving.line.payment"].reconcile_invoice_with_payment(
                        brw_line.saving_line_id.plan_ahorro_move_id.id, payment.id)
        self.saving_id.payment_ids=lines

        return {
            'name': 'Created Payment',
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'form',
            'res_id': payment.id,
        }

class AccountSavingPaymentLineWizard(models.TransientModel):
    _name = 'account.saving.payment.line.wizard'
    _description = 'Wizard to Create Account Payments from Saving Lines'

    wizard_id=fields.Many2one("account.saving.payment.wizard","Asistente")
    currency_id = fields.Many2one(related="wizard_id.currency_id", string='Moneda', store=False, readonly=True)
    number = fields.Integer(string='Número de cuota')
    date = fields.Date(string='Fecha de cuota')
    saving_line_id= fields.Many2one(
        'account.saving.lines',string="Linea de Ahorro")
    line_id=fields.Integer(string="# ID")
    pendiente=fields.Monetary(related="saving_line_id.pendiente",string="Pendiente",digits=(16,2))
    aplicado = fields.Float(string="Aplicado", digits=(16, 2))
