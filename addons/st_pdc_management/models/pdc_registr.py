# -*- coding: utf-8 -*-
##############################################################################
#
#    ODOO, Open Source Management Solution
#    Copyright (C) 2016 Steigend IT Solutions
#    For more details, check COPYRIGHT and LICENSE files
#
##############################################################################

from datetime import datetime
from odoo import models, api, fields, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class PdcRegistr(models.Model):
    _name = 'pdc.registr'
    _order = "name desc"


    name = fields.Char('Name')
    currency_id = fields.Many2one('res.currency', default=lambda s: s.env.user.company_id.currency_id.id)
    partner_id = fields.Many2one('res.partner', string="Partner")
    reg_date = fields.Date('Register Date', default=datetime.today())
    mature_date = fields.Date('Cheque Date/Mature Date')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('valid', 'Validated'),
        ('matured', 'Matured'),
        ('processed', 'Processed'),
        ('cancel', 'Cancelled')], default='draft', string="Status")
    cheque_amount = fields.Monetary('Cheque Amount')
    memo = fields.Char('Memo')
    cheque_no = fields.Char('Cheque No')
    bank_id = fields.Many2one('res.bank', string='Bank Name')
    payment_id = fields.Many2one('account.payment', 'Related Payment', ondelete='restrict')
    company_id = fields.Many2one('res.company', default=lambda s: s.env.user.company_id)
    payment_type = fields.Selection([('outbound', 'Send Money'), ('inbound', 'Receive Money')], string='Payment Type')


    @api.model
    def create(self, vals):
        if 'name' not in vals:
            if vals.get('payment_type') == 'outbound':
                sequence_code = 'cheque.pdc.payment'
                if vals.get('payment_id', False):
                    payment_obj = self.env['account.payment'].browse(vals.get('payment_id', False))
                    record_name = self.env['ir.sequence'].with_context(ir_sequence_date=payment_obj.date).next_by_code(
                        sequence_code)
                else:
                    record_name = self.env['ir.sequence'].next_by_code(sequence_code)
                vals.update({'name': record_name})

            if vals.get('payment_type') == 'inbound':
                sequence_code = 'cheque.pdc.receipt'
                if vals.get('payment_id', False):
                    payment_obj = self.env['account.payment'].browse(vals.get('payment_id', False))
                    record_name = self.env['ir.sequence'].with_context(ir_sequence_date=payment_obj.date).next_by_code(
                        sequence_code)
                else:
                    record_name = self.env['ir.sequence'].next_by_code(sequence_code)
                vals.update({'name': record_name})
        return super(PdcRegistr, self).create(vals)

    def unlink(self):
        if self.payment_id:
            raise UserError("Used In Payment. Can't Delete.")
        if self.state != 'draft':
            raise UserError('Deletion Blocked.')

    def action_validate(self):
        if self.mature_date > fields.Date.today():
            self.state = 'valid'
        else:
            self.state = 'matured'

    def action_process(self):
        if self.payment_id:
            self.payment_id.post_pdc()
        self.state = 'processed'

    @api.model
    def _maturity_check(self):
        PdcSudo = self.env['pdc.registr'].sudo()
        records = PdcSudo.search([('state', '=', 'valid')])
        one_day_after = fields.Date.today() + timedelta(days=1)
        for record in records:
            if record.mature_date == fields.Date.today() or \
                    record.mature_date < fields.Date.today() or \
                    record.mature_date == one_day_after:
                record.state = 'matured'
            else:
                pass
