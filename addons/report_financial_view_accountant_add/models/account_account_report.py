# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class CustomGeneralLedgerReport(models.Model):
    _inherit = 'account.report'

    def _report_custom_engine_nivel(self, line, options, expression, current_groupby, groupby, **kwargs):
        """
        Método personalizado para mostrar el primer dígito del código de cuenta.
        """
        print(line)
        print(options)
        print(expression)
        print(groupby)
        if line.account_id and line.account_id.level_code:
            return line.account_id.level_code
        return ''
