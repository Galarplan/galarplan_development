from odoo import models

class AccountReport(models.Model):
    _inherit = 'account.report'

    def get_html(self, options, lines=None):
        # Obtener la compañía actual
        company = self.env.company
        # Llamar al método original y agregar la compañía al contexto
        return super(AccountReport, self.with_context(company=company)).get_html(options, lines)