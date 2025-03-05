# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def action_draft(self):
        for brw_each in self:
            srch_lines=self.env["account.saving.line.payment"].sudo().search([('payment_id','=',brw_each.id)])
            if srch_lines:
                srch_lines.unlink()
        return super(AccountPayment, self).action_draft()

    def action_post(self):
        return super(AccountPayment, self).action_post()

    def action_cancel(self):
        for brw_each in self:
            srch_lines = self.env["account.saving.line.payment"].sudo().search([('payment_id', '=', brw_each.id)])
            if srch_lines:
                srch_lines.unlink()
        return super(AccountPayment, self).action_cancel()