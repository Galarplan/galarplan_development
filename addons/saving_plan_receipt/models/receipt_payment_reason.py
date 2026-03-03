from odoo import _, api, fields, models

class ReceiptPaymentReason(models.Model):
    _name = 'receipt.payment.reason'
    _description = 'Receipt Payment Reason'
    _rec_name = 'name'

    name = fields.Char(
        string='Nombre',
        required=True
    )

    code = fields.Char(
        string='Código',
        required=True
    )

    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company
    )

    _sql_constraints = [
        ('code_company_unique',
         'unique(code, company_id)',
         'El código debe ser único por compañía.')
    ]