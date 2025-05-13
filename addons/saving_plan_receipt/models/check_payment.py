from odoo import models, fields, api

class ReceiptValidation(models.Model):
    _name = 'receipt.validation'
    _description = 'Validación de Comprobantes de Pago'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char('Número de Comprobante', required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', 'Cliente', required=True, tracking=True)
    date = fields.Date('Fecha', default=fields.Date.context_today, tracking=True)
    amount = fields.Float('Monto', tracking=True)
    description = fields.Text('Descripción')
    attachment_id = fields.Binary('Comprobante Adjunto', attachment=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('posted', 'Publicado'),
        ('verified', 'Verificado'),
        ('rejected', 'Rechazado')
    ], string='Estado', default='draft', tracking=True)
    validated_by = fields.Many2one('res.users', 'Validado por', readonly=True)
    validation_date = fields.Datetime('Fecha de Validación', readonly=True)
    company_id = fields.Many2one('res.company', 'Compañía', default=lambda self: self.env.company)
    
    # Campos relacionados con el plan de ahorros
    saving_plan_id = fields.Many2one('account.saving', 'Plan de Ahorros')
    saving_line_id = fields.Many2one('account.saving.lines', 'Línea de Ahorro')
    
    def action_post(self):
        for rec in self:
            rec.state = 'posted'
    
    def action_verify(self):
        for rec in self:
            rec.write({
                'state': 'verified',
                'validated_by': self.env.user.id,
                'validation_date': fields.Datetime.now()
            })
    
    def action_reject(self):
        for rec in self:
            rec.state = 'rejected'
    
    def action_reset_to_draft(self):
        for rec in self:
            rec.state = 'draft'