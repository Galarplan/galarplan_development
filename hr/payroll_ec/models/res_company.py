# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
from odoo.exceptions import ValidationError,UserError
from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit="res.company"

    payslip_journal_id=fields.Many2one("account.journal","Diario de Nómina")