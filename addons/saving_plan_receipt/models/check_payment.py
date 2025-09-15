from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError
import base64

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

    is_data_updated = fields.Boolean('Datos Actualizados', default=False, tracking=True)
    
    date = fields.Date('Fecha', default=fields.Date.context_today, tracking=True)
    date_payment = fields.Date('Fecha Pago', default=fields.Date.context_today, tracking=True)
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

    payment_other_desc = fields.Char(
        string='Descripción de Otro Medio de Pago',
        tracking=True,
        help="Especifique el medio de pago cuando seleccione 'Otros'"
    )

    payment_reason = fields.Selection(
        selection='_compute_payment_reason',
        string='Motivo de pago',
        tracking = True,
    )

    saving_plan_payment = fields.Boolean('Plan de ahorro?',default=False)

    #campos adicionales para cheque, transferencia,deposito
    banco_emisor = fields.Many2one('res.bank','Banco Emisor')
    banco_receptor = fields.Many2one('res.bank','Banco Receptor')
    
    #campos adicionales cuando payment_from es cheque
    number_check = fields.Char('Numero de Cheque')
    account_check = fields.Char('Cuenta')
    date_check = fields.Date('fecha del cheque')
    
    #campos adicionales para tarjeta de credito
    credit_card = fields.Boolean('Es Tarjeta de credito')
    lote_card = fields.Char('# lote')
    card_number = fields.Char('# Tarjeta')


    #campos adicionales para transferencia y deposito
    comp_number = fields.Char('Numero de Comprobante')
    
    #campos adicional para transferencia
    acc_number = fields.Char('Numero de cuenta')

    #campos adicionales para otros
    cruce_cuentas = fields.Char('Cruce Cuentas')
    vehiculo_usado = fields.Text('Vehiculo Usado')



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
    
    def action_update_partner_data(self):
        """
        Actualiza los datos del contacto con la información del comprobante
        Solo accesible para administradores del módulo
        """
        self.ensure_one()
        
        # Verificar permisos - solo administradores del módulo pueden ejecutar esta acción
        if not self.env.user.has_group('saving_plan_receipt.group_validator_receipt_admin'):
            raise UserError(_('No tienes permisos para ejecutar esta acción. Solo los administradores pueden actualizar datos de contactos.'))
        
        if not self.partner_id:
            raise UserError(_('No hay un contacto asociado a este comprobante.'))
        
        # Guardar valores antiguos para el registro
        old_values = {
            'vat': self.partner_id.vat or '',
            'street': self.partner_id.street or '',
            'email': self.partner_id.email or ''
        }
        
        new_values = {
            'vat': self.document_number or '',
            'street': self.street or '',
            'email': self.mail_partner or ''
        }
        
        # Actualizar el contacto
        update_data = {}
        if self.document_number and self.document_number != self.partner_id.vat:
            update_data['vat'] = self.document_number
        
        if self.street and self.street != self.partner_id.street:
            update_data['street'] = self.street
        
        if self.mail_partner and self.mail_partner != self.partner_id.email:
            update_data['email'] = self.mail_partner
        
        if update_data:
            self.partner_id.write(update_data)
            
            # Crear mensaje para el chatter con los cambios
            change_messages = []
            for field, value in update_data.items():
                field_name = {
                    'vat': 'Documento',
                    'street': 'Dirección',
                    'email': 'Email'
                }.get(field, field)
                
                old_value = old_values.get(field, '')
                change_messages.append(
                    f"{field_name}: '{old_value}' → '{value}'"
                )
            
            # Mensaje para el chatter del comprobante
            message_body = _(
                "<b>Datos actualizados en el contacto:</b><br/>%s<br/>"
                "<b>Actualizado por:</b> %s"
            ) % ("<br/>".join(change_messages), self.env.user.name)
            
            self.message_post(body=message_body)
            
            # Mensaje para el chatter del contacto
            partner_message_body = _(
                "<b>Datos actualizados desde comprobante:</b> %s<br/>%s<br/>"
                "<b>Actualizado por:</b> %s"
            ) % (self.name, "<br/>".join(change_messages), self.env.user.name)
            
            self.partner_id.message_post(body=partner_message_body)
            
            # Marcar como actualizado
            self.is_data_updated = True
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Datos Actualizados'),
                    'message': _('Los datos del contacto han sido actualizados correctamente.'),
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Sin Cambios'),
                    'message': _('No se detectaron cambios en los datos para actualizar.'),
                    'type': 'warning',
                    'sticky': False,
                }
            }
    
    def print_receipt(self):
        self.ensure_one()
        
        # try:
        #     # Método seguro para Odoo 16
        #     uid = self.env['res.users'].authenticate(
        #         self.env.cr.dbname,
        #         self.usuario,
        #         self.password,
        #         {}
        #     )
        #     if not uid:
        #         raise ValidationError(_('Usuario o contraseña incorrectos'))
                
        #     user = self.env['res.users'].browse(uid)
        # except Exception as e:
        #     # raise ValidationError(_('Error de autenticación: %s') % str(e))
        #     raise ValidationError('Error de autenticación vuelve a cerrar la venta e ingresa nuevamente tus credenciales')
        
        # Verificar estado del recibo
        if self.state not in ('posted','verified'):
            raise ValidationError('El recibo debe estar en estado "Publicado" para poder imprimirse')
        
        # Registrar el usuario que imprime
        if not self.printed_by:
                self.printed_by = self.env.user.id,
                self.print_date = fields.Datetime.now()
            
        
        val = True
        if val:
            # Obtener la referencia del reporte
            report_ref = 'saving_plan_receipt.action_report_receipt_validation' 
            # Obtener el objeto report
            report = self.env['ir.actions.report']._get_report_from_name(report_ref)
            
            # Renderizar el reporte con todos los parámetros requeridos
            html_content, _ = report._render_qweb_html(
                report_ref=report_ref,
                docids=[self.id],
                data={}
            )
            
            # Codificar el contenido HTML en base64
            html_content_base64 = base64.b64encode(html_content)
            
            # Crear un adjunto temporal
            attachment = self.env['ir.attachment'].create({
                'name': f'Recibo_cobro_{self.name}.html',
                'type': 'binary',
                'datas': html_content_base64,
                'res_model': self._name,
                'res_id': self.id,
                'mimetype': 'text/html'
            })
            
            # Devolver acción para descargar el archivo
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/%s?download=true' % attachment.id,
                'target': 'new',
            }
        else:
        
            # Retornar la acción del reporte
            return self.env.ref('saving_plan_receipt.action_report_receipt_validation').report_action(self.receipt_id)
    
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