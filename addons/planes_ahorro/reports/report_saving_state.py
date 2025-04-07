from odoo import _, api, fields, models
from odoo.exceptions import UserError

import logging


_logger = logging.getLogger(__name__)




class ReportBudgetSummary(models.AbstractModel):
    _name = 'report.planes_ahorro.report_saving_state'
    _description = 'Reporte de Estado de cuenta'



    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Devuelve los valores utilizados por el template del reporte.
        """
        docs = self.env['account.saving'].browse(docids)
        company = self.env.company

        return {
            'doc_ids': docids,
            'doc_model': 'account.saving',
            'docs': docs,
            'company': company,
        }
    


    