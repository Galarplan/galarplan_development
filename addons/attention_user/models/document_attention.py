from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class DocumentAttention(models.Model):
    _name = 'document.attention'
    _description = 'Attention Documents'
    _order = 'date desc'

    attention_id = fields.Many2one('attention.user', string='Atención relacionada')
    date = fields.Date(string='Fecha de Emisión', default=fields.Date.context_today)
    client_id = fields.Many2one('res.partner', string='Cliente', required=True)
    codigo = fields.Char('Codigo')
    monto = fields.Float('Monto')
    income_date = fields.Date(string='Fecha Ingreso', default=fields.Date.context_today)
    paid_value = fields.Float(string='Valor Pagado')
    advisor_id = fields.Many2one("hr.employee", string="Asesor")
    commercial_manager_id = fields.Many2one("hr.employee", string="Jefe Comercial")
    reason_id = fields.Many2one('document.reason')
    document_detail = fields.Text(string='Detalle del documento')
    evidence = fields.Boolean(string='Evidencia')
    action_id = fields.Many2one('document.action')
    document_resolution = fields.Char('Resolucion Directorio')
    value_resolution = fields.Float('Valor Liquidado')
    date_resolution = fields.Date('Fecha Liquidacion')

    type_document = fields.Selection([
        ('contract','Contrato'),
        ('partial','Abono'),
        ('Sol','Solicitud')
    ],string="Tipo")

    action = fields.Selection([
        ('delivery', 'Entrega'),
        ('reception', 'Recepción'),
        ('review', 'Revisión'),
        ('approved', 'Aprovado')
    ], string='Acción')

    document_file = fields.Binary(
        string='Documento Adjunto',
        help="Suba el documento relacionado aquí"
    )
    
    # Nombre del archivo
    document_filename = fields.Char(
        string='Nombre del Archivo',
        help="Nombre del documento adjunto"
    )
    
    # Tipo de archivo (para validación)
    document_file_type = fields.Char(
        string='Tipo de Archivo',
        compute='_compute_file_type',
        store=True
    )
    
    @api.depends('document_file', 'document_filename')
    def _compute_file_type(self):
        for record in self:
            if record.document_filename:
                record.document_file_type = record.document_filename.split('.')[-1].lower()
            else:
                record.document_file_type = False
    
    # Validación del tipo de archivo
    @api.constrains('document_file', 'document_filename')
    def _check_document_file(self):
        allowed_extensions = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'png']
        for record in self:
            if record.document_filename and record.document_file_type not in allowed_extensions:
                raise ValidationError(
                    _("Tipo de archivo no permitido. Extensiones permitidas: %s") % 
                    ', '.join(allowed_extensions)
                )