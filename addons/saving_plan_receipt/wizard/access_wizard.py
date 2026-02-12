from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

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
    usuario = fields.Char('Usuario', required=True)
    password_receipt = fields.Char(
        string='Contraseña de Recibo',
        required=True,
        widget='password'
    )

    def action_open_receipt_form(self):
        self.ensure_one()
        
        # Buscar el usuario por login
        user = self.env['res.users'].sudo().search([('login', '=', self.usuario)], limit=1)
        
        if not user:
            raise ValidationError(_('Usuario no encontrado'))
        
        # Verificar si tiene contraseña de recibo configurada
        if not user.password_receipt:
            raise ValidationError(_('Este usuario no tiene configurada una contraseña de recibo'))
        
        # Verificar que la contraseña coincida
        if user.password_receipt != self.password_receipt:
            raise ValidationError(_('Contraseña de recibo incorrecta'))
        
        # Crear un nuevo registro de validación de comprobante
        receipt_vals = {
            'location_id': self.location_id.id,
            'company_id': self.company_id.id,
            'printed_by': user.id,
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