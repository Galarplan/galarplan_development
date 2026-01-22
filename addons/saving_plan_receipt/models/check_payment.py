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
    debit_card = fields.Boolean('Es Tarjeta de debito')
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
    
    # saving_line_id = fields.Many2many(
    #     'account.saving.lines', 
    #     domain="[('saving_id', '=', saving_plan_id), ('estado_pago', '=', 'pendiente')]"
    # )

    # Reemplazar en el modelo ReceiptValidation:
    saving_line_id = fields.One2many(
        'receipt.validation.savings',
        'receipt_id',
        string='Cuotas a Pagar',
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
            ('card_credit', 'Tarjeta de Credito'),
            ('card_debit','Tarjeta de Debito'),
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



    @api.onchange('amount', 'saving_plan_id')
    def _onchange_amount_auto_select_installments(self):
        """Selecciona automáticamente las cuotas basadas en el monto ingresado"""
        for record in self:
            
            if not record.amount or record.amount <= 0:
                record.saving_line_id = [(5, 0, 0)]
                return
            
            if not record.amount or not record.saving_plan_id or not record.saving_plan_payment:
                return
            
            # Limpiar cuotas existentes
            record.saving_line_id = [(5, 0, 0)]
            
            # Obtener cuotas pendientes ordenadas
            pending_installments = self.env['account.saving.lines'].search([
                ('estado_pago', '=', 'pendiente'),
                ('saving_id', '=', record.saving_plan_id.id)
            ], order='date asc, number asc')
            
            if not pending_installments:
                return
            
            remaining_amount = record.amount
            selected_installments = []
            
            # Verificar estado del plan
            plan_state = record.saving_plan_id.state
            
            if plan_state == 'adjudicated_with_assets':
                # Para adjudicados con activos: seleccionar cronológicamente
                selected_installments = self._select_chronological_installments(
                    pending_installments, remaining_amount
                )
            else:
                # Para otros estados: máximo 2 cuotas del inicio y el resto del final
                selected_installments = self._select_mixed_installments(
                    pending_installments, remaining_amount
                )
            
            # Crear las líneas seleccionadas
            for installment in selected_installments:
                record.saving_line_id = [(0, 0, {
                    'saving_line_id': installment.id,
                    'amount_to_pay': min(installment.pendiente, remaining_amount),
                    'is_full_payment': True
                })]
                remaining_amount -= installment.pendiente
    
    def _select_chronological_installments(self, pending_installments, amount):
        """Seleccionar cuotas cronológicamente (más antiguas primero)"""
        selected = []
        remaining = amount
        
        for installment in pending_installments:
            if remaining <= 0:
                break
            
            selected.append(installment)
            remaining -= installment.pendiente
        
        return selected
    
    def _select_mixed_installments(self, pending_installments, amount):
        """Seleccionar máximo 2 cuotas del inicio y el resto del final"""
        selected = []
        remaining = amount
        
        if not pending_installments:
            return selected
        
        # Convertir a lista para mejor manipulación
        installments_list = list(pending_installments)
        
        # Tomar máximo 2 cuotas del inicio
        start_count = min(2, len(installments_list))
        for i in range(start_count):
            if remaining <= 0:
                break
            
            installment = installments_list[i]
            selected.append(installment)
            remaining -= installment.pendiente
        
        # Si aún queda monto, tomar del final
        if remaining > 0 and len(installments_list) > start_count:
            # Tomar cuotas del final (más recientes)
            end_installments = installments_list[start_count:]
            # Ordenar descendente para tomar las más recientes primero
            end_installments_sorted = sorted(
                end_installments, 
                key=lambda x: (x.date or fields.Date.today(), x.number), 
                reverse=True
            )
            
            for installment in end_installments_sorted:
                if remaining <= 0:
                    break
                
                selected.append(installment)
                remaining -= installment.pendiente
        
        return selected
    
    @api.onchange('saving_line_id')
    def _onchange_saving_line_id_recalculate_amount(self):
        """Recalcular el monto total cuando se modifican las cuotas"""
        for record in self:
            if record.saving_line_id:
                total = sum(line.amount_to_pay for line in record.saving_line_id)
                record.amount = total
    
    # @api.depends('saving_line_id')
    # def _compute_installment_data(self):
    #     for record in self:
    #         # Números de cuotas pagadas como string
    #         paid_installments = record.saving_line_id.mapped('number')  # Ajusta 'numero_cuota' al nombre real del campo
    #         record.paid_installments_str = ", ".join(sorted(str(i) for i in paid_installments))
            
    #         # Sumar los valores de todas las cuotas seleccionadas
    #         record.saving_amount = sum(line.saving_amount for line in record.saving_line_id)  # Ajusta 'valor_cuota'
            
    #         # Valor de inscripción (si saving_amount es cero)
    #         # record.serv_admin_amount = sum(line.serv_admin_amount if record.saving_amount == 0 else 0
    #         record.serv_admin_amount = self.sum_inscription(record.saving_line_id)
    #         # Valor capital (principal)
    #         record.principal_amount = sum(line.principal_amount for line in record.saving_line_id)  # Ajusta 'principal_amount'
            
    #         # Gasto administrativo (si saving_amount no es cero)
    #         record.admin_expense_amount = self.sum_admin_expense(record.saving_line_id)
            
    #         # Valor del seguro
    #         record.insurance_amount = sum(line.seguro_amount for line in record.saving_line_id)  # Ajusta 'seguro_amount'
            
    #         # El amount debería ser la suma de todos estos valores
    #         record.amount = (
    #             record.saving_amount + 
    #             record.serv_admin_amount + 
    #             record.principal_amount + 
    #             record.admin_expense_amount + 
    #             record.insurance_amount
    #         )

    # @api.depends('saving_line_id')
    # def _compute_installment_data(self):
    #     for record in self:
    #         # Números de cuotas pagadas como string
    #         paid_installments = record.saving_line_id.mapped('installment_number')
    #         record.paid_installments_str = ", ".join(sorted(str(i) for i in paid_installments))
            
    #         # Sumar los valores de todas las cuotas seleccionadas
    #         record.saving_amount = sum(line.saving_line_id.saving_amount for line in record.saving_line_id)
            
    #         # Valor de inscripción (si saving_amount es cero)
    #         record.serv_admin_amount = sum(
    #             line.saving_line_id.serv_admin_amount 
    #             for line in record.saving_line_id 
    #             if line.saving_line_id.saving_amount == 0
    #         )
            
    #         # Valor capital (principal)
    #         record.principal_amount = sum(line.saving_line_id.principal_amount for line in record.saving_line_id)
            
    #         # Gasto administrativo (si saving_amount no es cero)
    #         record.admin_expense_amount = sum(
    #             line.saving_line_id.serv_admin_amount 
    #             for line in record.saving_line_id 
    #             if line.saving_line_id.saving_amount != 0
    #         )
            
    #         # Valor del seguro
    #         record.insurance_amount = sum(line.saving_line_id.seguro_amount for line in record.saving_line_id)
            
    #         # El amount debería ser la suma de todos estos valores
    #         # record.amount = (
    #         #     record.saving_amount + 
    #         #     record.serv_admin_amount + 
    #         #     record.principal_amount + 
    #         #     record.admin_expense_amount + 
    #         #     record.insurance_amount
    #         # )
    #         record.amount = (
    #             record.serv_admin_amount + 
    #             record.principal_amount + 
    #             record.admin_expense_amount + 
    #             record.insurance_amount
    #         )

    @api.depends('saving_line_id', 'saving_line_id.amount_to_pay', 
             'saving_line_id.is_full_payment',
             'saving_line_id.partial_serv_admin_amount',
             'saving_line_id.partial_principal_amount',
             'saving_line_id.partial_seguro_amount')
    def _compute_installment_data(self):
        for record in self:
            if not record.saving_line_id:
                record.paid_installments_str = ""
                record.saving_amount = 0
                record.serv_admin_amount = 0
                record.principal_amount = 0
                record.admin_expense_amount = 0
                record.insurance_amount = 0
                # No resetear record.amount aquí para que pueda ser ingresado manualmente
                continue
            
            # Números de cuotas pagadas como string
            paid_installments = record.saving_line_id.mapped('installment_number')
            record.paid_installments_str = ", ".join(sorted(str(i) for i in paid_installments))
            
            # Sumar saving_amount (valor cuota) de todas las cuotas
            record.saving_amount = sum(line.saving_line_id.saving_amount for line in record.saving_line_id)
            
            # Inicializar totales
            total_inscription = 0
            total_admin_expense = 0
            total_principal = 0
            total_insurance = 0
            
            for line in record.saving_line_id:
                if line.is_full_payment:
                    # Pago completo: usar montos completos
                    if line.saving_line_id.saving_amount == 0:
                        # Es inscripción
                        total_inscription += line.serv_admin_amount
                    else:
                        # Es gasto administrativo regular
                        total_admin_expense += line.serv_admin_amount
                    
                    total_principal += line.principal_amount
                    total_insurance += line.seguro_amount
                else:
                    # Pago parcial: usar montos proporcionales
                    if line.saving_line_id.saving_amount == 0:
                        # Es inscripción
                        total_inscription += line.partial_serv_admin_amount
                    else:
                        # Es gasto administrativo regular
                        total_admin_expense += line.partial_serv_admin_amount
                    
                    total_principal += line.partial_principal_amount
                    total_insurance += line.partial_seguro_amount
            
            record.serv_admin_amount = total_inscription
            record.admin_expense_amount = total_admin_expense
            record.principal_amount = total_principal
            record.insurance_amount = total_insurance
            
            # IMPORTANTE: Actualizar el monto total con la suma de componentes
            # Pero solo si hay cuotas seleccionadas
            if record.saving_line_id:
                record.amount = (
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
    
    def action_open_add_installments_wizard(self):
        self.ensure_one()
        return {
            'name': _('Seleccionar Cuotas'),
            'type': 'ir.actions.act_window',
            'res_model': 'add.installments.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_receipt_id': self.id,
                'active_id': self.id,
            }
        }
    
    def action_clear_installments(self):
        """Limpiar todas las cuotas seleccionadas"""
        self.ensure_one()
        if self.saving_line_id:
            self.saving_line_id.unlink()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Cuotas Eliminadas'),
                    'message': _('Todas las cuotas han sido eliminadas correctamente.'),
                    'type': 'success',
                    'sticky': False,
                }
            }
    

class ReceiptValidationSavings(models.Model):
    _name = 'receipt.validation.savings'
    _description = 'Líneas de pagos de planes'
    
    receipt_id = fields.Many2one(
        'receipt.validation',
        string='Comprobante',
        ondelete='cascade',
        required=True
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        related='receipt_id.company_id',
        store=True,
        readonly=True
    )
    
    # Otra opción: usar currency_id directamente
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        related='receipt_id.company_id.currency_id',
        store=True,
        readonly=True
    )
    
    saving_line_id = fields.Many2one(
        'account.saving.lines',
        string='Cuota del Plan',
        domain="[('estado_pago', '=', 'pendiente'), ('saving_id.partner_id', '=', parent.partner_id)]",
        required=True
    )
    
    # Datos de la cuota (copiados para referencia)
    installment_number = fields.Integer(
        string='Número de Cuota',
        related='saving_line_id.number',
        store=True,
        readonly=True
    )
    
    due_date = fields.Date(
        string='Fecha Vencimiento',
        related='saving_line_id.date',
        store=True,
        readonly=True
    )
    
    # Valores de la cuota
    saving_amount = fields.Monetary(
        string='Valor Cuota',
        related='saving_line_id.saving_amount',
        store=True,
        readonly=True
    )
    
    principal_amount = fields.Monetary(
        string='Valor Capital',
        related='saving_line_id.principal_amount',
        store=True,
        readonly=True
    )
    
    serv_admin_amount = fields.Monetary(
        string='Servicio Administrativo',
        related='saving_line_id.serv_admin_amount',
        store=True,
        readonly=True
    )
    
    seguro_amount = fields.Monetary(
        string='Valor Seguro',
        related='saving_line_id.seguro_amount',
        store=True,
        readonly=True
    )
    
    por_pagar = fields.Monetary(
        string='Por Pagar',
        related='saving_line_id.por_pagar',
        store=True,
        readonly=True
    )
    
    pendiente = fields.Monetary(
        string='Pendiente',
        related='saving_line_id.pendiente',
        store=True,
        readonly=True
    )
    
    pagos = fields.Monetary(
        string='Pagos Realizados',
        related='saving_line_id.pagos',
        store=True,
        readonly=True
    )
    
    estado_pago = fields.Selection(
        string='Estado de Pago',
        related='saving_line_id.estado_pago',
        store=True,
        readonly=True
    )
    
    # Campos para registro del pago
    amount_to_pay = fields.Monetary(
        string='Monto a Pagar',
        required=True,
        default=0.0,
        help='Monto específico a pagar de esta cuota'
    )
    
    is_full_payment = fields.Boolean(
        string='Pago Completo',
        default=True,
        help='Si es True, se paga el monto total pendiente. Si es False, se paga un monto parcial.'
    )
    
    # Campo para mostrar información de la cuota
    display_name = fields.Char(
        string='Descripción',
        compute='_compute_display_name',
        store=True
    )
    
    # Relación con el plan de ahorros
    saving_id = fields.Many2one(
        'account.saving',
        string='Plan de Ahorros',
        related='saving_line_id.saving_id',
        store=True,
        readonly=True
    )
    
    # Campos para diferenciar tipo de pago (cuota vs inscripción)
    is_inscription = fields.Boolean(
        string='Es Inscripción',
        compute='_compute_is_inscription',
        store=True
    )
    
    # Campos computados para pagos parciales
    partial_serv_admin_amount = fields.Monetary(
        string='Admin. Parcial',
        compute='_compute_partial_amounts',
        store=True
    )
    
    partial_principal_amount = fields.Monetary(
        string='Capital Parcial',
        compute='_compute_partial_amounts',
        store=True
    )
    
    partial_seguro_amount = fields.Monetary(
        string='Seguro Parcial',
        compute='_compute_partial_amounts',
        store=True
    )
    
    @api.depends('saving_line_id')
    def _compute_display_name(self):
        for record in self:
            if record.saving_line_id:
                plan_name = record.saving_line_id.saving_id.name or 'Sin Plan'
                cuota_num = record.saving_line_id.number or 'N/A'
                pendiente = record.saving_line_id.pendiente
                record.display_name = f"Plan: {plan_name} - Cuota {cuota_num} (Pendiente: {pendiente:.2f})"
            else:
                record.display_name = False
    
    @api.depends('saving_amount')
    def _compute_is_inscription(self):
        for record in self:
            # Si saving_amount es 0, es una inscripción
            record.is_inscription = record.saving_amount == 0
    
    @api.depends('amount_to_pay', 'pendiente', 'serv_admin_amount', 'principal_amount', 'seguro_amount', 'is_full_payment')
    def _compute_partial_amounts(self):
        """Calcula los montos proporcionales para pagos parciales"""
        for record in self:
            if not record.saving_line_id:
                record.partial_serv_admin_amount = 0
                record.partial_principal_amount = 0
                record.partial_seguro_amount = 0
                continue
            
            # Si es pago completo o pendiente es 0, usar los montos completos
            if record.is_full_payment or record.pendiente == 0:
                record.partial_serv_admin_amount = record.serv_admin_amount
                record.partial_principal_amount = record.principal_amount
                record.partial_seguro_amount = record.seguro_amount
            else:
                # Calcular proporción del pago
                if record.pendiente > 0:
                    proportion = record.amount_to_pay / record.pendiente
                    
                    # Aplicar proporción a cada componente
                    record.partial_serv_admin_amount = record.serv_admin_amount * proportion
                    record.partial_principal_amount = record.principal_amount * proportion
                    record.partial_seguro_amount = record.seguro_amount * proportion
                else:
                    record.partial_serv_admin_amount = 0
                    record.partial_principal_amount = 0
                    record.partial_seguro_amount = 0
    
    @api.onchange('saving_line_id')
    def _onchange_saving_line_id(self):
        """Al seleccionar una cuota, establecer el monto a pagar por defecto"""
        for record in self:
            if record.saving_line_id:
                # Por defecto, se paga el monto total pendiente
                record.amount_to_pay = record.saving_line_id.pendiente
                record.is_full_payment = True
    
    @api.onchange('is_full_payment', 'amount_to_pay')
    def _onchange_payment_details(self):
        """Validar que el monto a pagar no exceda el pendiente"""
        for record in self:
            if record.saving_line_id:
                if record.is_full_payment:
                    # Si es pago completo, establecer al pendiente total
                    record.amount_to_pay = record.saving_line_id.pendiente
                elif record.amount_to_pay > record.saving_line_id.pendiente:
                    record.amount_to_pay = record.saving_line_id.pendiente
    
    @api.constrains('amount_to_pay')
    def _check_amount_to_pay(self):
        """Validar que el monto a pagar sea válido"""
        for record in self:
            if record.amount_to_pay < 0:
                raise ValidationError('El monto a pagar no puede ser negativo')
            
            if record.saving_line_id and record.amount_to_pay > record.saving_line_id.pendiente:
                raise ValidationError(
                    f'El monto a pagar ({record.amount_to_pay}) no puede exceder '
                    f'el monto pendiente de la cuota ({record.saving_line_id.pendiente})'
                )
    
    def action_view_saving_line(self):
        """Abrir la vista de la cuota del plan"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cuota del Plan',
            'res_model': 'account.saving.lines',
            'res_id': self.saving_line_id.id,
            'view_mode': 'form',
            'target': 'current',
        }