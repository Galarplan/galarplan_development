from odoo import _, api, fields, models
from odoo.exceptions import UserError

class AccountPayment(models.Model):
    _inherit = 'account.payment'


    available_check_ids = fields.Many2many(
        comodel_name='payment.checkbook.line',
        compute='_compute_available_check_ids',
        string="Available Checks",
    )

    check_line_id = fields.Many2one(
        comodel_name='payment.checkbook.line',
        string="Check Number",
        domain="[('id', 'in', available_check_ids)]"
    )

    cheque_no = fields.Char(
        string="Check Number",
        readonly=True,
        store=True,
        compute='_compute_cheque_no'
    )

    @api.depends('check_line_id')
    def _compute_cheque_no(self):
        for payment in self:
            payment.cheque_no = payment.check_line_id.check_number if payment.check_line_id else False

    @api.depends('journal_id')
    def _compute_available_check_ids(self):
        for rec in self:
            rec.available_check_ids = [(5, 0, 0)]  # limpiar si no hay journal
            if rec.journal_id:
                check_lines = self.env['payment.checkbook.line'].search([
                    ('journal_id', '=', rec.journal_id.id),
                    ('is_used', '=', False)
                ])
                rec.available_check_ids = check_lines
            else:
                rec.available_check_ids = [(5, 0, 0)]  # limpiar si no hay journal

    
    def action_post(self):
        
        for payment in self:
            
            res = super().action_post()

            if payment.check_line_id:
                payment.check_line_id.is_used = True
                payment.check_line_id.payment_id = payment.id
                # Asegurar que cheque_no tenga el valor correcto
                payment.cheque_no = payment.check_line_id.check_number

        
        return res

    
    def action_post(self):

        if not self.cheque_no and self.payment_type == 'outbound' and self.payment_method_code in ['pdc','check_printing']:
            raise UserError('El metodo seleccionado es de tipo cheque pero no ha ingresado numero de cheque')
        if not self.check_line_id and self.payment_type == 'outbound' and self.payment_method_code in ['pdc','check_printing']:
            raise UserError('No has seleccionado un cheque del talonario')
        if not self.ref and self.payment_type == 'outbound' and self.payment_method_code in ['pdc','check_printing']:
            raise UserError('Debes especificar el uso del cheque')

        res = super().action_post()
        for payment in self:
            if payment.check_line_id:
                payment.check_line_id.is_used = True
                payment.check_line_id.payment_id = payment.id
                payment.check_line_id.reference = payment.ref
        return res