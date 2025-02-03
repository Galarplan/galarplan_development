# -*- coding: utf-8 -*-

from odoo import models, fields, api

MONTHS = {
    1: 'ENERO',
    2: 'FEBRERO',
    3: 'MARZO',
    4: 'ABRIL',
    5: 'MAYO',
    6: 'JUNIO',
    7: 'JULIO',
    8: 'AGOSTO',
    9: 'SEPTIEMBRE',
    10: 'OCTUBRE',
    11: 'NOVIEMBRE',
    12: 'DICIEMBRE',
}


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _l10n_ec_get_invoice_additional_info(self):
        # return {
        #     "Referencia": self.name,  # Reference
        #     "Vendedor": self.invoice_user_id.name or '',  # Salesperson
        #     "E-mail": self..email or '',
        # }
        if self.env.company.company_registry == 'BLP' and self.move_type == 'out_invoice':
          invoice_month = MONTHS.get(self.invoice_date.month)
          invoice_year = self.invoice_date.year
          return {
              "Referencia": self.payment_reference if self.payment_reference else f"Expensa Comunal {invoice_month} {invoice_year}",  # Reference
              "Cliente": self.partner_id.name or '',  # Salesperson
              "E-mail": self.partner_id.email or '',
              "direccion": self.partner_id.street or '',
          }
        else:
          return {
              "E-mail": self.partner_id.email or '',
              "direccion": self.partner_id.street or '',
          }