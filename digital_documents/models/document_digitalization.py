from odoo import models, fields, api

class DocumentDigitalization(models.Model):
    _name = 'document.digitalization'
    _description = 'Digitalization of Documents'

    name = fields.Char(string='Nombre del documento o Lote', required=True)
    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Attachments',
        help='Upload multiple files for this document or batch'
    )

    state = fields.Selection(
        [('draft', 'Draft'), ('complete', 'Complete')],
        string='Status',
        default='draft',
        required=True
    )

    @api.model
    def set_to_complete(self):
        """Method to change the status to Complete."""
        self.write({'state': 'complete'})
