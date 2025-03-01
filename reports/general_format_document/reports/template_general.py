from odoo import _, api, fields, models

import logging

_logger = logging.getLogger(__name__)




class TemplateGeneral(models.AbstractModel):
    _name = 'report.general_format_document.general_template'
    _description = 'Plantilla Documentos Generales'



    def _get_report_values(self, docids, data=None):
        docs = self.env['report.layout'].browse(docids)
        company = self.env.company  # Obtiene la compañía actual
        print("=============================================================",company)
        return {
            'docs': docs,
            'company': company,  # Pasa la compañía al contexto
        }


   

    