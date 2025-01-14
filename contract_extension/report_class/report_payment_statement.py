from odoo import models, api
from odoo.tools import format_date

class AccountStatementReport(models.AbstractModel):
    _name = "report.contract_extension.report_account_statement"
    _description = "Account Statement Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        print("Docids recibidos:", docids)
        contracts = self.env['contract.contract'].browse(docids)
        print("Contratos recuperados:", contracts)

        report_data = []
        for contract in contracts:
            related_invoices = contract._get_related_invoices()
            print(f"Facturas relacionadas para el contrato {contract.id}:", related_invoices)

            def get_payment_date(invoice):
                payment_lines = invoice.line_ids.filtered(lambda line: line.payment_id)
                return payment_lines.mapped("date")[-1].strftime('%d/%m/%Y') if payment_lines else ""

            invoice_lines = [
                {
                    "number": i,
                    "due_date": format_date(self.env, invoice.invoice_date_due) if invoice.invoice_date_due else "",
                    "payment_date": get_payment_date(invoice),
                    "amount": invoice.amount_total,
                    "paid_amount": invoice.amount_total - invoice.amount_residual,
                    "remaining": invoice.amount_residual,
                    "status": "Pagado" if invoice.amount_residual == 0 else "Pendiente",
                }
                for i, invoice in enumerate(related_invoices, start=1)
            ]
            print(f"Líneas de facturas para el contrato {contract.id}:", invoice_lines)

            report_data.append({
                "contract_id": contract.id,
                "partner_name": contract.partner_id.name,
                "cedula": contract.partner_id.vat or "N/A",
                "plan_code": contract.code or "N/A",
                "plan_type": contract.plan_type or "N/A",
                "amount": contract.amount_plan or 0.0,
                "currency": contract.currency_id.name or "N/A",
                "start_date": format_date(self.env, contract.date_start) if contract.date_start else "",
                "end_date": format_date(self.env, contract.date_end) if contract.date_end else "",
                "invoice_lines": invoice_lines,
            })

        print('Reporte generado:', report_data)
        return {
            "docs": contracts,
            "data": report_data,
        }
