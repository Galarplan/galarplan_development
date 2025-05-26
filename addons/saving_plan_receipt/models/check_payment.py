from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ReceiptValidation(models.Model):
    _name = 'receipt.validation'
    _description = 'Validación de Comprobantes de Pago'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(
        string='Número de Comprobante',
        required=True,
        tracking=True,
        copy=False,
        readonly=True,
        default=lambda self: _('Borrador'),
    )
    partner_id = fields.Many2one('res.partner', 'Cliente', required=True, tracking=True)
    mail_partner = fields.Char(
        string='Email',
        compute='_compute_mail',
        store=True,
        readonly=False  # Permite edición manual si es necesario
    )
    date = fields.Date('Fecha', default=fields.Date.context_today, tracking=True)
    amount = fields.Float('Monto', tracking=True)
    description = fields.Text('Descripción')
    attachment_id = fields.Many2many(comodel_name='ir.attachment', relation='receipt_documents', string='Adjuntar Documentos')
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('posted', 'Publicado'),
        ('verified', 'Verificado'),
        ('rejected', 'Rechazado')
    ], string='Estado', default='draft', tracking=True)
    validated_by = fields.Many2one('res.users', 'Validado por', readonly=True)
    validation_date = fields.Datetime('Fecha de Validación', readonly=True)
    company_id = fields.Many2one('res.company', 'Compañía', default=lambda self: self.env.company)
    payment_form = fields.Selection(
        selection='_compute_payment_form_selection',
        string='Forma de Pago',
        tracking=True
    )
    
    # Campos relacionados con el plan de ahorros
    saving_plan_id = fields.Many2one(
        'account.saving', 
        'Plan de Ahorros',
        domain="[('partner_id', '=', partner_id)]"
    )
    
    saving_line_id = fields.Many2one(
        'account.saving.lines', 
        'Línea de Ahorro',
        domain="[('saving_id', '=', saving_plan_id), ('estado_pago', '=', 'pendiente')]"
    )


    @api.depends('partner_id')
    def _compute_mail(self):
        for record in self:
            record.mail_partner = record.partner_id.email if record.partner_id else False

    @api.depends_context('company_id')
    def _compute_payment_form_selection(self):
        # Opciones base
        base_options = [
            ('transfer', 'Transferencia'),
            ('check', 'Cheque'),
            ('cash', 'Efectivo'),
            ('card', 'Tarjeta de Credito')
        ]
        
        # Aquí puedes añadir lógica para obtener opciones adicionales dinámicamente
        # Por ejemplo, de parámetros del sistema, otra tabla, etc.
        additional_options = self._get_additional_payment_forms()
        
        return base_options + additional_options

    def _get_additional_payment_forms(self):
        """Método para obtener formas de pago adicionales"""
        # Ejemplo: obtener de parámetros de configuración
        # Puedes personalizar esto según tus necesidades
        additional_forms = []
        
        # Ejemplo: añadir una opción desde parámetros del sistema
        # if self.env['ir.config_parameter'].sudo().get_param('add_digital_wallet', False):
        #     additional_forms.append(('digital_wallet', 'Billetera Digital'))
            
        # También podrías consultar otra tabla/modelo que almacene formas de pago
        # payment_types = self.env['payment.type'].search([])
        # additional_forms.extend([(pt.code, pt.name) for pt in payment_types])
        
        return additional_forms

    
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
    
    

    def get_report_data(self):
        self.ensure_one()
        return {
            'doc': self,
            'preliminary': self.state == 'posted',
            'complete': self.state == 'verified',
        }
    
    @api.model
    def create(self, vals):
        """
        Sobrescribe el método create para asignar automáticamente
        el número de comprobante usando la secuencia definida
        """
        if not vals.get('name') or vals.get('name') == _('Borrador'):
            # Obtener la secuencia definida en XML
            sequence_code = 'receipt_payment'
            
            # Generar el número de secuencia
            vals['name'] = self.env.company.company_registry + self.env['ir.sequence'].next_by_code(sequence_code)
        
        return super(ReceiptValidation, self).create(vals)