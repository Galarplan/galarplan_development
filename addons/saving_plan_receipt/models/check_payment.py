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
    partner_id = fields.Many2one('res.partner', 'Cliente', tracking=True)
    
    document_number = fields.Char(
        string='Documento',
        compute='_compute_mail',
        store=True  # Permite edición manual si es necesario
    )
    
    street = fields.Char(
        string='Direccion',
        compute='_compute_mail',
        store=True  # Permite edición manual si es necesario
    )

    mail_partner = fields.Char(
        string='Email',
        compute='_compute_mail',
        store=True  # Permite edición manual si es necesario
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
    validated_by = fields.Many2one('res.users', 'Validado por')
    asesor_id = fields.Many2one('res.users','Asesor')
    validation_date = fields.Datetime('Fecha de Validación', tracking=True)
    company_id = fields.Many2one('res.company', 'Compañía', default=lambda self: self.env.company)

    location_id = fields.Many2one('location.places',string='Ubicacion', domain="[('company_id', '=', company_id)]")
    
    payment_form = fields.Selection(
        selection='_compute_payment_form_selection',
        string='Forma de Pago',
        tracking=True
    )

    payment_reason = fields.Selection(
        selection='_compute_payment_reason',
        string='Motivo de pago',
        tracking = True,
    )

    saving_plan_payment = fields.Boolean('Plan de ahorro?',default=False)

    
    # Campos relacionados con el plan de ahorros
    saving_plan_id = fields.Many2one(
        'account.saving', 
        'Plan de Ahorros',
        domain="[('partner_id', '=', partner_id)]"
    )
    
    saving_line_id = fields.Many2many(
        'account.saving.lines', 
        domain="[('saving_id', '=', saving_plan_id), ('estado_pago', '=', 'pendiente')]"
    )

    paid_installments_str = fields.Char(
        string="Cuotas Pagadas",
        compute="_compute_installment_data",
        store=True,
        tracking = True
    )
    saving_amount = fields.Float(
        string="Valor Cuotas",
        compute="_compute_installment_data",
        store=True,
        tracking = True
    )
    serv_admin_amount = fields.Float(
        string="Valor Inscripción",
        compute="_compute_installment_data",
        store=True,
        tracking = True
    )
    principal_amount = fields.Float(
        string="Valor Capital",
        compute="_compute_installment_data",
        store=True,
        tracking = True
    )
    admin_expense_amount = fields.Float(
        string="Gasto Administrativo",
        compute="_compute_installment_data",
        store=True,
        tracking = True
    )
    insurance_amount = fields.Float(
        string="Valor Seguro",
        compute="_compute_installment_data",
        store=True,
        tracking = True
    )
    
    printed_by = fields.Many2one('res.users', 'Impreso por', readonly=True)
    print_date = fields.Datetime('Fecha de impresión', readonly=True)



    def action_open_print_wizard(self):
        return {
            'name': _('Imprimir Recibo'),
            'type': 'ir.actions.act_window',
            'res_model': 'print.receipt.wz',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_receipt_id': self.id},
        }


    @api.depends('partner_id')
    def _compute_mail(self):
        for record in self:
            record.mail_partner = record.partner_id.email if record.partner_id else False
            record.document_number = record.partner_id.vat if record.partner_id else False
            record.street = record.partner_id.street if record.partner_id else False

    @api.depends_context('company_id')
    def _compute_payment_form_selection(self):
        # Opciones base
        base_options = [
            ('cash', 'Efectivo'),
            ('check', 'Cheque'),
            ('card', 'Tarjeta de Credito'),
            ('transfer', 'Transferencia'),
            ('deposit','Deposito'),
            ('other','Otros')
        ]
        
        # Aquí puedes añadir lógica para obtener opciones adicionales dinámicamente
        # Por ejemplo, de parámetros del sistema, otra tabla, etc.
        additional_options = self._get_additional_payment_forms()
        
        return base_options + additional_options
    
    @api.depends_context('company_id')
    def _compute_payment_reason(self):
        base_options = [
            ('inscrip', 'Inscripcion'),
            ('quota', 'Cuota Plan'),
            ('lici', 'Licitación'),
            ('save', 'Seguro Vehicular'),
            ('disp','Dispositivo'),
            ('legal_waste','Gastos Legales')
        ]
        
        # Aquí puedes añadir lógica para obtener opciones adicionales dinámicamente
        # Por ejemplo, de parámetros del sistema, otra tabla, etc.
        
        
        return base_options
    
    def sum_inscription(self,lines):
        value = 0
        for line in lines:
            if line.saving_amount == 0:
                value += line.serv_admin_amount
        return value
    
    def sum_admin_expense(self,lines):
        value = 0
        for line in lines:
            if line.saving_amount != 0:
                value += line.serv_admin_amount
        return value

    
    @api.depends('saving_line_id')
    def _compute_installment_data(self):
        for record in self:
            # Números de cuotas pagadas como string
            paid_installments = record.saving_line_id.mapped('number')  # Ajusta 'numero_cuota' al nombre real del campo
            record.paid_installments_str = ", ".join(sorted(str(i) for i in paid_installments))
            
            # Sumar los valores de todas las cuotas seleccionadas
            record.saving_amount = sum(line.saving_amount for line in record.saving_line_id)  # Ajusta 'valor_cuota'
            
            # Valor de inscripción (si saving_amount es cero)
            # record.serv_admin_amount = sum(line.serv_admin_amount if record.saving_amount == 0 else 0
            record.serv_admin_amount = self.sum_inscription(record.saving_line_id)
            # Valor capital (principal)
            record.principal_amount = sum(line.principal_amount for line in record.saving_line_id)  # Ajusta 'principal_amount'
            
            # Gasto administrativo (si saving_amount no es cero)
            record.admin_expense_amount = self.sum_admin_expense(record.saving_line_id)
            
            # Valor del seguro
            record.insurance_amount = sum(line.seguro_amount for line in record.saving_line_id)  # Ajusta 'seguro_amount'
            
            # El amount debería ser la suma de todos estos valores
            record.amount = (
                record.saving_amount + 
                record.serv_admin_amount + 
                record.principal_amount + 
                record.admin_expense_amount + 
                record.insurance_amount
            )

   


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
            rec.validated_by = ''
    

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
            # print('locacion==========================',vals['location_id'],)
            
            if vals.get('location_id'):
                # Generar el número de secuencia
                name_pre = self.env['ir.sequence'].next_by_code(sequence_code)
                name_pre_list = name_pre.split('-')
                location_places_id = self.env['location.places'].browse(vals['location_id'])

                vals['name'] = f"{name_pre_list[0]}-{location_places_id.code}-{name_pre_list[1]}"
            else:
                raise UserError('Debes Colocar la ubicacion donde se hace el cobro ')
        
        return super(ReceiptValidation, self).create(vals)