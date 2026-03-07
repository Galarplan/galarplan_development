from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

class AssignSavingLinesWz(models.TransientModel):
    _name = 'assign.saving.lines.wz'
    _description = 'Aplicar Pago a Cuotas'

    receipt_id = fields.Many2one(
        'receipt.validation',
        required=True
    )

    user_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        required=True
    )

    saving_id = fields.Many2one(
        'account.saving',
        string='Plan',
        domain="[('partner_id','=',user_id)]",
        required=True
    )

    saving_lines_ids = fields.Many2many(
        'account.saving.lines',
        string='Cuotas Pendientes',
        domain="[('saving_id','=',saving_id), ('estado_pago','=','pendiente')]",
        required=True
    )

    def assign_payment(self):
        self.ensure_one()

        remaining_amount = self.receipt_id.amount

        lines = self.saving_lines_ids.sorted('date')

        for line in lines:
            if remaining_amount <= 0:
                break

            pending = line.pendiente

            if pending <= 0:
                continue

            amount_to_apply = min(remaining_amount, pending)

            self.env['receipt.saving.payment'].create({
                'receipt_id': self.receipt_id.id,
                'saving_line_id': line.id,
                'amount': amount_to_apply
            })

            remaining_amount -= amount_to_apply

        if remaining_amount > 0:
            raise ValidationError(
                f"Sobran {remaining_amount} sin aplicar."
            )

        self.receipt_id.state = 'applicated'
        
        return {
        'type': 'ir.actions.act_window',
        'name': 'Plan de Ahorro',
        'res_model': 'account.saving',
        'view_mode': 'form',
        'res_id': self.saving_id.id,
        'target': 'current',
    }