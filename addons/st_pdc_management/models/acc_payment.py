# -*- coding: utf-8 -*-
##############################################################################
#
#    ODOO, Open Source Management Solution
#    Copyright (C) 2016 Steigend IT Solutions
#    For more details, check COPYRIGHT and LICENSE files
#
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime

global_status = {
    'draft': 'Draft',
    'on_pdc': 'On PDC',
    'posted': 'Posted',
    'cancel': 'Cancel'
}


class AccountPaymentMethod(models.Model):
    _inherit = "account.payment.method"

    @api.model
    def _get_payment_method_information(self):
        res = super(AccountPaymentMethod, self)._get_payment_method_information()
        res.update({
            'pdc': {'mode': 'multi', 'domain': [('type', 'in', ('bank', 'cash'))]},
            
        })
        return res


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def action_draft(self):
        previous_status = self and self[0].state or ''
        previous_status_value = global_status.get(previous_status) or ''
        res = super(AccountPayment, self).action_draft()
        for rec in self:

            if rec.pdc_register_id:
                rec.pdc_register_id.state = 'draft'
            self.sudo().message_post(body=('Status: %s → Draft') % (
                previous_status_value))
        return res

    def action_cancel(self):
        previous_status = self and self[0].state or ''
        previous_status_value = global_status.get(previous_status) or ''
        res = super(AccountPayment, self).action_cancel()
        for rec in self:
            if rec.pdc_register_id:
                rec.pdc_register_id.state = 'cancel'
            self.sudo().message_post(body=('Status: %s → Cancel') % (
                previous_status_value))
        return res

    @api.depends('journal_id')
    def get_journal_bank(self):
        for record in self:
            record.bank_id = record.journal_id and record.journal_id.bank_id and record.journal_id.bank_id.id or False

    bank_id = fields.Many2one('res.bank', string='Bank')
    pdc_register_id = fields.Many2one('pdc.registr', 'Post Dated Cheque', copy=False)
    mature_date = fields.Date('Cheque Maturing Date', copy=False)
    cheque_no = fields.Char('Cheque No')

    def set_to_draft(self):
        if self.move_id:
            to_reconcile = self.move_id.mapped('line_ids').filtered('reconciled')
            to_reconcile.remove_move_reconcile()
            self.move_id.unlink()

        previous_status = self and self[0].state or ''
        previous_status_value = global_status.get(previous_status) or ''
        self.state = 'draft'

        self.sudo().message_post(body=('Status: %s → Draft') % (
            previous_status_value))
        if self.pdc_registr_id:
            self.pdc_registr_id.write({
                'state': 'cancel'
            })

    @api.onchange('journal_id')
    def onchange_journal_id(self):
        self.bank_id = self.journal_id and self.journal_id.bank_id and self.journal_id.bank_id.id or False

    
    def write(self, vals):
        res = super(AccountPayment, self).write(vals)
        
        if 'payment_method_id' in vals and self.payment_method_code in ['cheque','pdc','check_printing'] and self.cheque_id:
            raise UserError('Sorry You Cannot change Payment Method of this Payment,'
                            ' Because you already create a Cheque.')
            
        return res

    def action_reconfirm(self):
        for record in self:
            previous_status = record.state or ''
            previous_status_value = global_status.get(previous_status) or ''
            record.state = 'posted'
            record.sudo().message_post(body=('Status: %s → Posted') % (
                previous_status_value))

    def _update_bank_in_payment(self):
        all_payments = self.env['account.payment'].search([('bank_id', '=', False)])
        for items in all_payments:
            items.bank_id = items.journal_id and items.journal_id.bank_id and items.journal_id.bank_id.id or False

    def create_cheque_register(self):
        pdc_registr = self.env['pdc.registr']
        if self.pdc_register_id and self.pdc_register_id.state == 'cancel':
            take_old_name = self.pdc_register_id.name or ''
            return pdc_registr.create({
                'payment_id': self.id,
                'name': take_old_name,
                'partner_id': self.partner_id and self.partner_id.id or False,
                'reg_date': self.date,
                'mature_date': self.mature_date,
                'cheque_amount': self.amount,
                'memo': self.ref,
                'cheque_no': self.cheque_no,
                'bank_id': self.bank_id and self.bank_id.id or False,
                'payment_type': self.payment_type
            })

        else:
            return pdc_registr.create({
                'payment_id': self.id,
                'partner_id': self.partner_id.id,
                'reg_date': self.date,
                'mature_date': self.mature_date,
                'cheque_amount': self.amount,
                'memo': self.ref,
                'cheque_no': self.cheque_no,
                'bank_id': self.bank_id.id,
                'payment_type': self.payment_type
            })

    def action_post(self):
        if self.amount <= 0.0:
            raise UserError('Payment amount should be positive')
        for rec in self:
            if rec.cheque_no:
                print("rrrr",rec.cheque_no)
                check_similar_records = self.env['pdc.registr'].search([('cheque_no', '=', rec.cheque_no)])
                if check_similar_records and len(check_similar_records) > 1:
                    raise UserError("Warning!! Duplicating Cheque Number...Use another Cheque no!!")

        if self.payment_method_code == 'pdc':
            return self.process_pdc_method()
        previous_status = self and self[0].state or ''
        previous_status_value = global_status.get(previous_status) or ''
        res = super(AccountPayment, self).action_post()
        self.sudo().message_post(body=('Status: %s → Posted') % (
            previous_status_value))
        return res

    def post_pdc(self):
        previous_status = self and self[0].state or ''
        previous_status_value = global_status.get(previous_status) or ''
        self.state = 'draft'
        self.sudo().message_post(body=('Status: %s → Draft') % (
            previous_status_value))
        self.date = self.mature_date or fields.Datetime.now()
        return super(AccountPayment, self).action_post()

    def process_pdc_method(self):
        pdc_register_obj = self.create_cheque_register()
        pdc_register_obj.action_validate()
        if self.pdc_register_id:
            self.pdc_register_id.payment_id = False
            self.pdc_register_id.state = 'draft'
            self.pdc_register_id.unlink()

        record_name = self.name or 'Draft Payment'

        previous_status = self and self[0].state or ''
        previous_status_value = global_status.get(previous_status) or ''
        self.write({
            'state': 'on_pdc',
            'name': record_name,
            'pdc_register_id': pdc_register_obj.id,
        })
        
        self.sudo().message_post(body=('Status: %s → On PDC') % (
            previous_status_value))
