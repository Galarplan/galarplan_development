from odoo import models, fields, api, _
from odoo.exceptions import ValidationError,UserError

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    other_payment = fields.Boolean(string='Otros Pagos')
    counterpart_account_id = fields.Many2one(
        'account.account', 
        string='Cuenta Contrapartida',
        domain="[('deprecated', '=', False)]"
    )


    

    def _create_payment_entry(self, amount):
        # Si no es un "Otro Pago" o no se seleccionó una cuenta contrapartida, usar el comportamiento original
        if not self.other_payment or not self.counterpart_account_id:
            return super(AccountPayment, self)._create_payment_entry(amount)

        # Crear el asiento contable manualmente
        move_vals = self._prepare_move_vals()
        move = self.env['account.move'].create(move_vals)

        # Crear la línea de débito (cuenta de banco)
        debit_line_vals = {
            'name': self.name,
            'amount_currency': -amount if self.payment_type == 'outbound' else amount,
            'currency_id': self.currency_id.id,
            'debit': amount if self.payment_type == 'outbound' else 0.0,
            'credit': 0.0 if self.payment_type == 'outbound' else amount,
            'account_id': self.journal_id.default_account_id.id,
            'partner_id': self.partner_id.id,
            'move_id': move.id,
        }
        self.env['account.move.line'].create(debit_line_vals)

        # Crear la línea de crédito (cuenta contrapartida seleccionada)
        credit_line_vals = {
            'name': self.name,
            'amount_currency': amount if self.payment_type == 'outbound' else -amount,
            'currency_id': self.currency_id.id,
            'debit': 0.0 if self.payment_type == 'outbound' else amount,
            'credit': amount if self.payment_type == 'outbound' else 0.0,
            'account_id': self.counterpart_account_id.id,
            'partner_id': self.partner_id.id,
            'move_id': move.id,
        }
        self.env['account.move.line'].create(credit_line_vals)

        # Validar el asiento contable
        move.action_post()

        return move
    


    def action_create_payment_entry(self):
        """
        Método personalizado para crear el movimiento contable manualmente.
        """
        for payment in self:
            # Verificar si el pago ya tiene un movimiento contable
            if payment.move_id:
                raise UserError(_("Este pago ya tiene un movimiento contable asociado."))
            
            # Llamar al método _create_payment_entry para crear el movimiento contable
            move = payment._create_payment_entry(payment.amount)
            
            # Mostrar un mensaje de confirmación
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Movimiento contable creado'),
                    'message': _('El movimiento contable se ha creado correctamente.'),
                    'type': 'success',
                    'sticky': False,
                }
            }
    

    # def action_post(self):
    #     # Llamar al método original para procesar el pago
    #     res = super(AccountPayment, self).action_post()

    #     # Verificar si es un "Otro Pago" y si se seleccionó una cuenta contrapartida
    #     for payment in self:
    #         if payment.other_payment and payment.counterpart_account_id:
    #             move = payment.move_id

    #             # Buscar la línea del pago que corresponde a la cuenta de banco
    #             bank_line = move.line_ids.filtered(
    #                 lambda line: line.account_id == payment.journal_id.default_account_id
    #             )

    #             # Buscar la línea del pago que corresponde a la cuenta contrapartida
    #             counterpart_line = move.line_ids.filtered(
    #                 lambda line: line.account_id == payment.counterpart_account_id
    #             )

    #             # Si ambas líneas existen, realizar el cruce contable
    #             if bank_line and counterpart_line:
    #                 (bank_line + counterpart_line).reconcile()

    #     return res

    # def action_post(self):
    #     for payment in self:
    #         # Si es un "Otro Pago" y se seleccionó una cuenta contrapartida
    #         if payment.other_payment and payment.counterpart_account_id:
    #             # Deshabilitar la reconciliación automática con facturas
    #             payment = payment.with_context(skip_account_move_synchronization=True)

    #             # Crear el movimiento contable manualmente
    #             move = payment._create_payment_entry(payment.amount)

    #             # Buscar las líneas contables del movimiento
    #             bank_line = move.line_ids.filtered(
    #                 lambda line: line.account_id == payment.journal_id.default_account_id
    #             )
    #             counterpart_line = move.line_ids.filtered(
    #                 lambda line: line.account_id == payment.counterpart_account_id
    #             )

    #             # Realizar la reconciliación entre las líneas de banco y contrapartida
    #             if bank_line and counterpart_line:
    #                 (bank_line + counterpart_line).reconcile()

    #             # Mostrar un mensaje de confirmación
    #             payment.message_post(body=_("Movimiento contable creado correctamente."))
    #             return {
    #                 'type': 'ir.actions.client',
    #                 'tag': 'display_notification',
    #                 'params': {
    #                     'title': _('Éxito'),
    #                     'message': _('El movimiento contable se ha creado y reconciliado correctamente.'),
    #                     'type': 'success',
    #                     'sticky': False,
    #                 }
    #             }

    #         # Si no es un "Otro Pago", usar el comportamiento original
    #         return super(AccountPayment, payment).action_post()

    def action_post(self):
        """Sobreescribe el método action_post para manejar pagos con cuenta contrapartida"""
        # Si es un pago con other_payment activado y tiene cuenta contrapartida
        for payment in self.filtered(lambda p: p.other_payment and p.counterpart_account_id):
            # Validar que la cuenta contrapartida esté definida
            if not payment.counterpart_account_id:
                raise UserError(_('Por favor, seleccione una cuenta contrapartida para este pago.'))

            # Preparar los valores del movimiento contable manualmente
            move_vals = {
                'date': payment.date,
                'ref': payment.ref,
                'journal_id': payment.journal_id.id,
                'company_id': payment.company_id.id,
                'state': 'draft',
            }
            
            # Obtener la cuenta de liquidez (cuenta de banco) original
            liquidity_account = payment.journal_id.default_account_id
            
            if not liquidity_account:
                raise UserError(_('El diario seleccionado no tiene una cuenta de liquidez configurada.'))

            # Modificar las líneas del asiento
            move_lines = [
                # Línea de débito/crédito en la cuenta de banco
                {
                    'name': payment.ref,
                    'account_id': liquidity_account.id,
                    'debit': payment.amount if payment.payment_type == 'inbound' else 0.0,
                    'credit': payment.amount if payment.payment_type == 'outbound' else 0.0,
                    'journal_id': payment.journal_id.id,
                    'partner_id': payment.partner_id.id,
                    'payment_id': payment.id,
                    'company_id': payment.company_id.id,
                },
                # Línea de contrapartida
                {
                    'name': payment.ref,
                    'account_id': payment.counterpart_account_id.id,
                    'debit': payment.amount if payment.payment_type == 'outbound' else 0.0,
                    'credit': payment.amount if payment.payment_type == 'inbound' else 0.0,
                    'journal_id': payment.journal_id.id,
                    'partner_id': payment.partner_id.id,
                    'payment_id': payment.id,
                    'company_id': payment.company_id.id,
                }
            ]
            
            # Actualizar los valores del asiento
            move_vals['line_ids'] = [(0, 0, line) for line in move_lines]
            
            # Crear y validar el asiento
            move = self.env['account.move'].with_context(default_move_type='entry').create(move_vals)
            move.action_post()
            
            # Registrar el pago con el asiento
            payment.write({
                'state': 'posted',
                'move_id': move.id,
            })
            
        # Para los pagos que no usan other_payment, usar el comportamiento original
        super(AccountPayment, self - self.filtered('other_payment')).action_post()
        
        return True

    @api.constrains('other_payment', 'counterpart_account_id')
    def _check_counterpart_account(self):
        """Validación para asegurar que si other_payment está activo, haya una cuenta contrapartida"""
        for payment in self:
            if payment.other_payment and not payment.counterpart_account_id:
                raise ValidationError(_('Debe especificar una cuenta contrapartida cuando "Otros Pagos" está activado.'))