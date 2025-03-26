# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.misc import xlsxwriter
import io


class GeneralLedgerXlsxReport(models.AbstractModel):
    _name = 'report.report_financial_view_accountant.ledger_report.xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, records):
        sheet = workbook.add_worksheet('General Ledger')
        bold = workbook.add_format({'bold': True})

        # Column headers
        headers = ['Fecha', 'Empresa', 'Diario', 'Referencia', 'Debe', 'Haber', 'Acumulado']
        for col, header in enumerate(headers):
            sheet.write(0, col, header, bold)

        row = 1
        for record in records:
            for line in record.line_ids:
                sheet.write(row, 0, str(line.date))
                sheet.write(row, 1, line.partner_id.name if line.partner_id else '')
                sheet.write(row, 2, line.journal_id.name if line.journal_id else '')
                sheet.write(row, 3, line.name)
                sheet.write(row, 4, line.debit)
                sheet.write(row, 5, line.credit)
                sheet.write(row, 6, line.amount_accumulated)
                row += 1