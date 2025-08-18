from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import base64

class PrintReceiptWizard(models.TransientModel):
    _name='print.receipt.wz'
    _description = 'impresion de recibo'


   

    usuario = fields.Char('Usuario')
    password = fields.Char('Contraseña')
    receipt_id = fields.Many2one('receipt.validation', string='Recibo')


    def print_receipt(self):
        self.ensure_one()
        
        try:
            # Método seguro para Odoo 16
            uid = self.env['res.users'].authenticate(
                self.env.cr.dbname,
                self.usuario,
                self.password,
                {}
            )
            if not uid:
                raise ValidationError(_('Usuario o contraseña incorrectos'))
                
            user = self.env['res.users'].browse(uid)
        except Exception as e:
            # raise ValidationError(_('Error de autenticación: %s') % str(e))
            raise ValidationError('Error de autenticación vuelve a cerrar la venta e ingresa nuevamente tus credenciales')
        
        # Verificar estado del recibo
        if self.receipt_id.state not in ('posted','verified'):
            raise ValidationError('El recibo debe estar en estado "Publicado" para poder imprimirse')
        
        # Registrar el usuario que imprime
        if not self.receipt_id.printed_by:

            self.receipt_id.write({
                'printed_by': user.id,
                'print_date': fields.Datetime.now()
            })
        
        val = False
        if val:
            # Obtener la referencia del reporte
            report_ref = 'saving_plan_receipt.action_report_receipt_validation' 
            # Obtener el objeto report
            report = self.env['ir.actions.report']._get_report_from_name(report_ref)
            
            # Renderizar el reporte con todos los parámetros requeridos
            html_content, _ = report._render_qweb_html(
                report_ref=report_ref,
                docids=[self.receipt_id.id],
                data={}
            )
            
            # Codificar el contenido HTML en base64
            html_content_base64 = base64.b64encode(html_content)
            
            # Crear un adjunto temporal
            attachment = self.env['ir.attachment'].create({
                'name': f'Recibo_cobro_{self.receipt_id.name}.html',
                'type': 'binary',
                'datas': html_content_base64,
                'res_model': self.receipt_id._name,
                'res_id': self.receipt_id.id,
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
    
    @api.model
    def default_get(self, fields):
        res = super(PrintReceiptWizard, self).default_get(fields)
        if self._context.get('active_id'):
            res['receipt_id'] = self._context['active_id']
        return res
