from odoo import _, api, fields, models

class AccountSavingLines(models.Model):
    _inherit = 'account.saving.lines'
    
    payment_receipt_ids = fields.One2many(
        'receipt.saving.payment',
        'saving_line_id'
    )

    paid_receipt_amount = fields.Float(
        compute='_compute_paid_receipt_amount',
        store=True
    )

    pending_receipt_amount = fields.Float(
        compute='_compute_paid_receipt_amount',
        store=True
    )

    @api.depends('payment_ids.amount')
    def _compute_paid_receipt_amount(self):
        for line in self:
            total_paid = sum(line.payment_receipt_ids.mapped('amount'))
            line.paid_receipt_amount = total_paid
            line.pending_receipt_amount = line.pendiente - total_paid
    
