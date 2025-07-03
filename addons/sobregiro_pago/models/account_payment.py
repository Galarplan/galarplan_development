# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    cuenta_giro_id = fields.Many2one('account.account', string="Cuenta de Giro (6xx)")#, domain="[('code', '=like', '6%')]")


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    sobregiro = fields.Boolean(string="Sobregiro")
    cuenta_sobregiro_id = fields.Many2one('account.account', string="Cuenta de Contrapartida (7xx)")#, domain="[('code', '=like', '7%')]")

    def action_post(self):
        for payment in self:
            if payment.sobregiro:
                payment._apply_sobregiro_logic()
            else:
                super(AccountPayment, payment).action_post()
        return True

    def _apply_sobregiro_logic(self):
        for payment in self:
            if not payment.journal_id.cuenta_giro_id:
                raise UserError(_("Debe configurar la Cuenta de Giro (6xx) en el diario."))
            if not payment.cuenta_sobregiro_id:
                raise UserError(_("Debe seleccionar la Cuenta de Contrapartida (7xx)."))

            amount = abs(payment.amount)

            # Crear asiento contable personalizado sin usar la lógica de pagos
            move_vals = {
                'ref': payment.name or '/',
                'date': payment.date,
                'journal_id': payment.journal_id.id,
                'partner_id': payment.partner_id.id,
                'line_ids': [
                    (0, 0, {
                        'name': 'Sobregiro - Cuenta de Giro',
                        'account_id': payment.journal_id.cuenta_giro_id.id,
                        'debit': amount,
                        'credit': 0.0,
                        'partner_id': payment.partner_id.id,
                    }),
                    (0, 0, {
                        'name': 'Sobregiro - Cuenta 7xx',
                        'account_id': payment.cuenta_sobregiro_id.id,
                        'debit': 0.0,
                        'credit': amount,
                        'partner_id': payment.partner_id.id,
                    }),
                ],
            }

            move = self.env['account.move'].create(move_vals)
            move.action_post()

            # Registrar manualmente que ya está hecho el pago
            payment.write({
                'state': 'posted',
                'move_id': move.id,
            })
