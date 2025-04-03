from odoo import _, api, fields, models

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
        res = super().action_post()
        for payment in self:
            if payment.check_line_id:
                payment.check_line_id.is_used = True
                payment.check_line_id.payment_id = payment.id
        return res