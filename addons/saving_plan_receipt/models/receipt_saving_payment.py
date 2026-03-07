from odoo import _, api, fields, models

class ReceiptSavingPayment(models.Model):
    _name = 'receipt.saving.payment'
    _description = 'Aplicación de Recibo a Cuota'

    receipt_id = fields.Many2one(
        'receipt.validation',
        required=True,
        ondelete='cascade'
    )

    saving_line_id = fields.Many2one(
        'account.saving.lines',
        required=True,
        ondelete='cascade'
    )

    amount = fields.Float(required=True)