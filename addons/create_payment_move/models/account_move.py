from odoo import _, api, fields, models

class AccountMove(models.Model):
    _inherit = 'account.move'


    def creat_payment_move(self):
        print('====================================',self.id)
        print(self.journal_id.read())
        vals = {
            'move_id':self.id,
            'payment_method_line_id':self.journal_id.inbound_payment_method_line_ids[0].id,
            'currency_id':self.env.company.currency_id.id,
            'partner_id': self.partner_id.id,
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'amount':self.amount_total_signed,
            'amount_residual':self.amount_total_signed
        }
        # self.env['account.payment'].create(vals)


        # Construir la consulta SQL
        query = """
            INSERT INTO account_payment (
                move_id, payment_method_line_id, currency_id, partner_id, payment_type,
                partner_type, amount, amount_residual
            ) VALUES (
                %(move_id)s, %(payment_method_line_id)s, %(currency_id)s, %(partner_id)s,
                %(payment_type)s, %(partner_type)s, %(amount)s, %(amount_residual)s
            ) RETURNING id;
        """
        self.env.cr.execute(query, vals)
        payment_id = self.env.cr.fetchone()[0]  # Obtener el ID del pago creado
        print('==================================',vals)

        # Redireccionar al pago creado
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'res_id': payment_id,
            'view_mode': 'form',
            'target': 'current',
        }
        