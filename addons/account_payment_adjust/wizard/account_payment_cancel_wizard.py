from odoo import api, fields, models


class AccountPaymentCancelWizard(models.TransientModel):
    _name = 'account.payment.cancel.wizard'
    _description = 'Wizard to Cancel Payment by Creating a Reverse Payment'

    @api.model
    def _get_default_payment_id(self):
        return self.env.context.get('active_id')

    date = fields.Date(string='Fecha de Reverso', required=True, default=fields.Date.context_today)
    payment_id = fields.Many2one('account.payment', string='Pago', required=True,default=_get_default_payment_id)
    comments=fields.Text("Comentarios")

    def action_reverse_payment(self):
        OBJ_PERIOD_LINE = self.env["account.fiscal.year.line"].sudo()
        self.ensure_one()
        if not self.payment_id:
            return

        # Desconciliar líneas de pago
        move_lines = self.payment_id.move_id.line_ids.filtered(lambda l: l.account_id.reconcile)
        move_lines.remove_move_reconcile()

        # Determinar el tipo de pago opuesto
        reversed_payment_type = 'inbound' if self.payment_id.payment_type == 'outbound' else 'outbound'

        brw_period, brw_period_line = OBJ_PERIOD_LINE.get_periods(self.date, self.payment_id.company_id,
                                                                  for_account_move=False,
                                                                  for_stock_move_line=False,
                                                                  for_account_payment=True)

        # Crear el pago inverso
        payment_line_ids=[(5,)]
        if self.payment_id.change_payment:
            for line in self.payment_id.payment_line_ids:
                payment_line_ids+=[(0,0,{   'debit': line.credit,
                    'credit': line.debit,
                    'account_id':line.account_id.id,
                    'partner_id':line.partner_id and line.partner_id.id or False,
                    'name':line.name,
                                            'ref_contrapartida':line.ref_contrapartida

                })]


        reversed_payment = self.payment_id.copy({
            'payment_type': reversed_payment_type,
            'date': self.date,
            'amount': self.payment_id.amount,
            'journal_id': self.payment_id.journal_id.id,
            'partner_id': self.payment_id.partner_id.id,
            'ref': f"Reverso de {self.payment_id.name}",
            'state': 'draft',
            'reversed_payment_id':self.payment_id.id,
            'change_payment':self.payment_id.change_payment,
            'is_prepayment':self.payment_id.is_prepayment,
            'prepayment_account_id':self.payment_id.prepayment_account_id and self.payment_id.prepayment_account_id.id or False,
            "period_id":brw_period and brw_period.id or False,
            "period_line_id":brw_period_line and brw_period_line.id or False,
            "payment_line_ids":payment_line_ids
        })

        if self.comments:
            reversed_payment.message_post(body=self.comments)

        if self.payment_id.is_prepayment:
            reversed_payment.write({"is_prepayment": False})
            reversed_payment=reversed_payment.with_context(skip_account_move_synchronization=False)
            reversed_payment._synchronize_from_moves(['is_prepayment','prepayment_account_id'])#para actualizar en caso de ser necesario el debe y el haber
            reversed_payment.write({"is_prepayment":True})
        else:
            reversed_payment._synchronize_to_moves(['amount','change_payment','payment_line_ids'])#para actualizar en caso de ser necesario el debe y el haber
        # Validar el nuevo pago si es necesario
        reversed_payment.action_post()

        # Conciliar el nuevo asiento con las líneas originales
        accounts= reversed_payment.move_id.line_ids.mapped('account_id').filtered(lambda l: l.reconcile)
        for account in accounts:
            new_move_lines = reversed_payment.move_id.line_ids.filtered(lambda l: l.account_id==account and l.account_id.reconcile)
            old_move_lines=self.payment_id.move_id.line_ids.filtered(lambda l: l.account_id==account and l.account_id.reconcile)
            (old_move_lines + new_move_lines).reconcile()

        ###
        self.payment_id.reversed_payment_id=reversed_payment.id

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'form',
            'res_id': reversed_payment.id,
        }


