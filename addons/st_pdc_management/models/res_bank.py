# -*- coding: utf-8 -*-
##############################################################################
#
#    ODOO, Open Source Management Solution
#    Copyright (C) 2016 Steigend IT Solutions
#    For more details, check COPYRIGHT and LICENSE files
#
##############################################################################
from odoo import models, fields


class CustomBank(models.Model):
    _inherit = 'res.bank'
    _description = 'Custom Bank'

    bank_code = fields.Char(string='Bank Code')
    iban_code = fields.Char(string='IBAN Code')



