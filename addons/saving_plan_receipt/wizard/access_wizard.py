from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError

class ReceiptAccessWizard(models.TransientModel):
    _name = 'receipt.access.wizard'
    _description = 'Wizard de Acceso a Validación de Comprobantes'

    location_id = fields.Many2one(
        'location.places', 
        string='Ubicación', 
        required=True,
        domain="[('company_id', '=', company_id)]"
    )
    company_id = fields.Many2one(
        'res.company', 
        string='Compañía', 
        default=lambda self: self.env.company
    )
    # partner_id = fields.Many2one('res.partner', string='Cliente')
    # saving_plan_payment = fields.Boolean('Plan de ahorro?', default=False)
    usuario = fields.Char('Usuario')
    password = fields.Char('Contraseña')

    def action_open_receipt_form(self):
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
        
        
        
        
        # Crear un nuevo registro de validación de comprobante
        receipt_vals = {
            'location_id': self.location_id.id,
            'company_id': self.company_id.id,
            # 'partner_id': self.partner_id.id if self.partner_id else False,
            # 'saving_plan_payment': self.saving_plan_payment,
        }
        
        new_receipt = self.env['receipt.validation'].create(receipt_vals)
        
        # Retornar la acción para abrir el formulario
        return {
            'name': _('Validación de Comprobante'),
            'type': 'ir.actions.act_window',
            'res_model': 'receipt.validation',
            'res_id': new_receipt.id,
            'view_mode': 'form',
            'target': 'current',
            'context': self.env.context,
        }