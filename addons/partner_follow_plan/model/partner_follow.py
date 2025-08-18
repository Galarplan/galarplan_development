from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

class PartnerFollow(models.Model):
    _name = 'partner.follow'
    _description = 'Informacion de planes'
    check_company=True
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec = 'sequence'
    # ============ Cabecera Datos del cliente =======================
    company_id = fields.Many2one('res.company',default = lambda self: self.env.company.id)
    sequence = fields.Char('Documento N')
    nombre_cliente = fields.Char('Nombre del Cliente')
    document_number = fields.Char('CI/RUC')
    fecha_solicitud = fields.Date('Fecha Solicitud')
    fecha_recepcion = fields.Date('Fecha Recepcion')
    phone = fields.Char('Telefono')
    calle = fields.Char('Calle')
    correo = fields.Char('Correo Electronico')
    fecha_pago = fields.Selection([('1','1 al 5'),('2','15 al 19'),('3','15 al 20'),('4','15 al 25')])
    codigo_plan = fields.Char('Codigo')
    fecha_contrato = fields.Char('Fecha Contrato')
    tipo_plan = fields.Selection([('normal','Normal'),('financiamiento','Financiamiento')])
    plan_id = fields.Many2one('account.saving.plan','Plan')
    monto = fields.Float('Monto', compute = '_compute_plan_data',store=True)
    plazo = fields.Float('Plazo',compute = '_compute_plan_data',store=True)
    inscripcion = fields.Float('Inscripcion',compute = '_compute_plan_data',store=True)
    inscripcion_si = fields.Float('Inscripcion Sin Iva',compute = '_compute_plan_data',store=True)
    iva = fields.Float('IVA',compute = '_compute_plan_data',store=True)
    first_pay = fields.Float('1era Cuota',compute = '_compute_plan_data',store=True)
    total_first_pay = fields.Float('Total 1er Cuota',compute = '_compute_plan_data',store=True)
    payment_amount = fields.Float('Valor cancelado')
    adicional = fields.Float('Abono Adicional', compute= '_compute_payment', store=True)
    cxc_mount = fields.Float('Saldo Por Cobrar',compute= '_compute_payment', store=True)
    quota_calc = fields.Float('Cuotas Adelantadas',compute= '_compute_payment', store=True)
    #================ Datos de venta =============
    asesor = fields.Many2one('hr.employee','Asesor')
    jefe = fields.Many2one('hr.employee','Jefe')
    agencia = fields.Many2one('location.places','Agencia')
    gerente_comercial = fields.Many2one('hr.employee','Gerente Comercial')
    gerente_general = fields.Many2one('hr.employee','Gerente General')

    #=================Opcion de Entregables =====================
    solicitud_admision = fields.Boolean('Solicitud de admisión')
    documentos_personales = fields.Boolean('Documentos Personales')
    pagina_control = fields.Boolean('Página de Control')
    pago_completado = fields.Boolean('Pago Completado')
    contrato_firmado = fields.Boolean('Contrato Firmado')
    total_requisitos = fields.Integer(
        '# Requisitos Presentados',
        compute='_compute_total_requisitos',
        store=True
    )
    #==========================Preguntas====================
    preq1 = fields.Boolean('Pregunta 1')
    preq2 = fields.Boolean('Pregunta 2')
    preq3 = fields.Boolean('Pregunta 3')

    solicitud_status = fields.Selection([('draft','Borrador'),('confirmed','Confirmado'),('approved','Aprobado')],default='draft',tracking=True)
    partner_status = fields.Selection([('n','No Contactado'),('s','Contactado')],default='n')
    plan_created = fields.Boolean('Plan Creado')
    partner_id = fields.Many2one('res.partner')
    saving_id = fields.Many2one('account.saving')
    



    @api.depends('plan_id')
    def _compute_plan_data(self):
        for record in self:
            record.monto = record.plan_id.saving_amount
            record.plazo = record.plan_id.periods
            record.inscripcion = record.plan_id.saving_amount*(record.plan_id.rate_inscription/100)
            record.inscripcion_si = (record.plan_id.saving_amount*(record.plan_id.rate_inscription/100))/(1.15)
            record.iva = (record.plan_id.saving_amount*(record.plan_id.rate_inscription/100))*(0.15)
            record.first_pay = record.plan_id.quota_amount
            record.total_first_pay = record.inscripcion + record.plan_id.quota_amount
    
    @api.depends('payment_amount', 'total_first_pay', 'first_pay')
    def _compute_payment(self):
        for record in self:
            # Calculate adicional amount
            record.adicional = record.payment_amount - record.total_first_pay 
            
            # Handle negative adicional (debt)
            if record.adicional < 0:
                record.cxc_mount = abs(record.adicional)
                record.quota_calc = 0.0  # Reset quota calc when there's debt
            else:
                # Handle division by zero case
                if record.first_pay != 0:
                    record.quota_calc = record.adicional / record.first_pay
                else:
                    record.quota_calc = 0.0
                record.cxc_mount = 0.0  # Reset debt when payment is sufficient

    @api.depends(
        'solicitud_admision',
        'documentos_personales',
        'pagina_control',
        'pago_completado',
        'contrato_firmado'
    )
    def _compute_total_requisitos(self):
        for record in self:
            total = 0
            if record.solicitud_admision:
                total += 1
            if record.documentos_personales:
                total += 1
            if record.pagina_control:
                total += 1
            if record.pago_completado:
                total += 1
            if record.contrato_firmado:
                total += 1
            record.total_requisitos = total

    
    def approve_state(self):
        for record in self:
            record.solicitud_status = 'approved'
    
    def confirmed_state(self):
        for record in self:
            record.solicitud_status = 'confirmed'
    
    def draft_state(self):
        for record in self:
            record.solicitud_status = 'draft'
    
    def creater_partner_plan(self):
        for record in self:
            # Validación 1: Verificar que el documento no esté vacío
            if not record.document_number:
                raise ValidationError(_("El número de documento (CI/RUC) es obligatorio para crear el plan"))
            
            # Validación 2: Verificar que no exista otro partner con el mismo document_number
            existing_partner = self.env['res.partner'].search([
                ('vat', '=', record.document_number)
            ], limit=1)
            
            if existing_partner:
                raise ValidationError(_("Ya existe un cliente con el documento %s") % record.document_number)
            
            existing_plan = self.env['account.saving'].search([('name','=',record.codigo_plan)])

            if existing_plan:
                raise ValidationError(_('Ya Existe Un Plan Creado con ese Codigo %s')%(record.codigo_plan))

            # Validación 3: Verificar que esté en estado confirmado
            if record.solicitud_status != 'confirmed':
                raise ValidationError(_("Solo puedes crear planes desde estado 'Confirmado'"))
            
            # Validación 4: Verificar que tenga un plan seleccionado
            if not record.plan_id:
                raise ValidationError(_("Debes seleccionar un plan de ahorro"))
            


            # Creación del partner
            partner_vals = {
                'name': record.nombre_cliente,
                'vat': record.document_number,
                'phone': record.phone,
                'email': record.correo,
                'street': record.calle,
                # Agrega aquí otros campos necesarios para tu partner
            }
            new_partner = self.env['res.partner'].create(partner_vals)
            
            # Creación del plan de ahorro
            saving_vals = {
                'name': record.codigo_plan,
                'partner_id': new_partner.id,
                'saving_plan_id': record.plan_id.id,
                'start_date': fields.Date.today(),
                'saving_type': record.tipo_plan,
                'seller_id': record.asesor.id,
                # 'is_direct': True,  # o el tipo de venta correspondiente
            }
            new_saving = self.env['account.saving'].create(saving_vals)
            
            # Actualizar el estado y los campos de relación
            record.write({
                'solicitud_status': 'approved',
                'partner_id': new_partner.id,
                'saving_id': new_saving.id,
                'plan_created': True,
            })
            
            # Opcional: Abrir el plan creado en una nueva ventana
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.saving',
                'res_id': new_saving.id,
                'view_mode': 'form',
                'target': 'current',
                'context': self.env.context,
            }





