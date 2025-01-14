from odoo import models, fields, api
from datetime import datetime
import calendar
import base64
import io
import xlsxwriter
import pandas as pd


class UAFEReportWizard(models.TransientModel):
    _name = "uafe.report.wizard"
    _description = "Reporte UAFE"

    month = fields.Selection(
        [
            ("1", "Enero"),
            ("2", "Febrero"),
            ("3", "Marzo"),
            ("4", "Abril"),
            ("5", "Mayo"),
            ("6", "Junio"),
            ("7", "Julio"),
            ("8", "Agosto"),
            ("9", "Septiembre"),
            ("10", "Octubre"),
            ("11", "Noviembre"),
            ("12", "Diciembre"),
        ],
        string="Mes",
        required=True,
    )

    date_start = fields.Date(string="Fecha de Inicio", readonly=True, store=True)
    date_end = fields.Date(string="Fecha de Fin", readonly=True, store=True)
    company_id = fields.Many2one(
        "res.company", string="Compañía", default=lambda self: self.env.company
    )
    invoice_ids = fields.One2many(
        comodel_name="uafe.report.wizard.line",  # Nombre del modelo relacionado
        inverse_name="wizard_id",  # Relación inversa
        string="Facturas",
    )

    registro_number_customer = fields.Char(string="Número de Registro cliente")
    registro_number_operation = fields.Char(string="Número de Registro Operaciones")

    file_name = fields.Char("File Name", readonly=True)
    file_data = fields.Binary("File", readonly=True)

    def load_invoices(self):
        """Cargar las facturas en el rango de fechas."""
        if not self.date_start or not self.date_end:
            year = datetime.today().year
            month = int(self.month)
            self.date_start = datetime(year, month, 1)
            last_day = calendar.monthrange(year, month)[1]
            self.date_end = datetime(year, month, last_day)

        invoices = self.env["account.move"].search(
            [
                ("invoice_date", ">=", self.date_start),
                ("invoice_date", "<=", self.date_end),
                ("company_id", "=", self.company_id.id),
                ("state", "=", "posted"),
                ("is_vehicle", "=", True),
            ]
        )
        lines = []
        for invoice in invoices:
            lines.append(
                (
                    0,
                    0,
                    {
                        "invoice_id": invoice.id,
                        "partner_name": invoice.partner_id.name,
                        "invoice_date": invoice.invoice_date,
                        "amount_total": invoice.amount_total,
                    },
                )
            )
        print(lines)
        self.invoice_ids = lines

        # Acción para recargar el wizard sin cerrar
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
        }

    @api.onchange("month")
    def _onchange_month(self):
        """Actualiza las fechas según el mes seleccionado."""
        if self.month:
            year = datetime.today().year
            start_day = datetime(year, int(self.month), 1)
            last_day = calendar.monthrange(year, int(self.month))[1]
            end_day = datetime(year, int(self.month), last_day)
            self.date_start = start_day
            self.date_end = end_day

    def _get_invoices(self):
        """Devuelve las facturas en el rango de fechas."""
        invoices = self.env["account.move"].search(
            [
                ("invoice_date", ">=", self.date_start),
                ("invoice_date", "<=", self.date_end),
                ("company_id", "=", self.company_id.id),
                ("state", "=", "posted"),
                ("is_vehicle", "=", True),
            ]
        )
        print("Facturas obtenidas en _get_invoices:", invoices)
        return invoices

    @api.depends("date_start", "date_end")
    def _compute_invoices(self):
        """Carga las facturas en el campo invoice_ids."""
        for record in self:
            invoices = record._get_invoices()
            record.invoice_ids = invoices

    def generate_clients_excel(self):
        """Genera el reporte de clientes con encabezado doble."""

        # Fecha de corte validada
        fecha_corte = (
            self.date_end.strftime("%Y%m%d")
            if self.date_end
            else datetime.now().strftime("%Y%m%d")
        )

        # Datos del encabezado general y de los clientes
        general_data = [
            [
                "IDENTIFICACION DEL REPORTE",
                "CODIGO DE REGISTRO",
                "PERIODO",
                "NUMERO DE REGISTRO",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
            ]
        ]
        detailed_header = [
            [
                "TIPO IDENTIFICACIÓN (TID)",
                "IDENTIFICACIÓN (IDE)",
                "NOMBRES APELLIDOS RAZÓN SOCIAL (NRS)",
                "NACIONALIDAD (NAC)",
                "DIRECCIÓN (DIR)",
                "CANTÓN (CCC)",
                "ACTIVIDAD ECONOMICA (AEC)",
                "INGRESO MENSUAL (IMT)",
                "CÓDIGO REGISTRO (CDR)",
                "FECHA CORTE (FCT)",
            ]
        ]
        client_data = [
            [
                "CLI",
                self.company_id.uafe_code,
                fecha_corte,
                self.registro_number_customer,
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
            ]
        ]

        # Filas de clientes
        for invoice in self.invoice_ids:
            partner = invoice.invoice_id.partner_id
            client_data.append(
                [
                    partner.l10n_latam_identification_type_id.name or "",
                    partner.vat or "",
                    partner.name or "",
                    partner.country_id.nationality_code or "",
                    partner.street or "",
                    partner.country_substate_id.code or "",
                    partner.economic_activity.code or "",
                    partner.monthly_income or "",
                    self.company_id.uafe_code,
                    fecha_corte,
                ]
            )

        # Crear archivo Excel
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet("Clientes")

        # Formato para las celdas
        bold_format = workbook.add_format(
            {"bold": True, "bg_color": "#FFFF00", "border": 1, "align": "center"}
        )
        normal_format = workbook.add_format({"border": 1, "align": "center"})

        # Escribir las filas del encabezado
        for row, row_data in enumerate(general_data + detailed_header):
            for col, value in enumerate(row_data):
                worksheet.write(row, col, value, bold_format)

        # Escribir datos de los clientes
        for row, row_data in enumerate(client_data, start=2):
            for col, value in enumerate(row_data):
                worksheet.write(row, col, value, normal_format)

        workbook.close()
        output.seek(0)

        # Guardar el archivo como adjunto
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"CLI_{timestamp}.xlsx"
        file_data = base64.b64encode(output.read())

        attachment = self.env["ir.attachment"].create(
            {
                "name": file_name,
                "datas": file_data,
                "type": "binary",
                "res_model": "uafe.report.wizard",
                "res_id": self.id,
            }
        )

        # Descargar el archivo
        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{attachment.id}?download=true",
            "target": "self",
        }

    def generate_operations_excel(self):
        """Genera el reporte de clientes con encabezado doble."""

        # Fecha de corte validada
        fecha_corte = (
            self.date_end.strftime("%Y%m%d")
            if self.date_end
            else datetime.now().strftime("%Y%m%d")
        )

        # Datos del encabezado general y de los clientes
        general_data = [
            [
                "IDENTIFICACION DEL REPORTE",
                "CODIGO DE REGISTRO",
                "PERIODO",
                "NUMERO DE REGISTRO",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
            ]
        ]
        detailed_header = [
            [
                "TIPO IDENTIFICACIÓN (TID)",
                "IDENTIFICACIÓN (IDE)",
                "NUMERO DE OPERACIÓN/CONTRATO (NCT)",
                "VALOR TOTAL DE LA OPERACIÓN (VTO)",
                "FECHA DE OPERACIÓN (FDO)",
                "TIPO DE VEHICULO O MAQUINARIA (TVHM)",	
                "MODELO DE VEHICULO O MAQUINARIA (MVHM)",
                "MARCA DE VEHICULO O MAQUINARIA (MAVM)"	,
                "CHASIS DE VEHICULO O MAQUINARIA (NCVM)",
                "CANTON O CIUDAD DEL VEHICULO O MAQUINARIA (CCT)",
                "FECHA CORTE (FCT)",
                "CÓDIGO REGISTRO (CDR)",
            ]
        ]
        client_data = [
            [
                "OPR",
                self.company_id.uafe_code,
                fecha_corte,
                self.registro_number_customer,
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
            ]
        ]
        for invoice in self.invoice_ids:
            partner = invoice.invoice_id.partner_id
            for line in invoice.invoice_id.invoice_line_ids:
                product_id = line.product_id
                client_data.append(
                    [
                        partner.l10n_latam_identification_type_id.name or "",
                        partner.vat or "",
                        "",
                        line.price_unit or "",
                        invoice.invoice_date or "",
                        product_id.vehicle_type.name or "",
                        product_id.name or "",
                        product_id.vehicle_model_id.name or "",
                        product_id.chassis_number or "",
                        partner.country_substate_id.code or "",
                        fecha_corte,
                        self.company_id.uafe_code,

                    ]
                )
        # Crear archivo Excel
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet("Operaciones")

        # Formato para las celdas
        bold_format = workbook.add_format(
            {"bold": True, "bg_color": "#FFFF00", "border": 1, "align": "center"}
        )
        normal_format = workbook.add_format({"border": 1, "align": "center"})

        # Escribir las filas del encabezado
        for row, row_data in enumerate(general_data + detailed_header):
            for col, value in enumerate(row_data):
                worksheet.write(row, col, value, bold_format)

        # Escribir datos de los clientes
        for row, row_data in enumerate(client_data, start=2):
            for col, value in enumerate(row_data):
                worksheet.write(row, col, value, normal_format)

        workbook.close()
        output.seek(0)

        # Guardar el archivo como adjunto
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"OPR_{timestamp}.xlsx"
        file_data = base64.b64encode(output.read())

        attachment = self.env["ir.attachment"].create(
            {
                "name": file_name,
                "datas": file_data,
                "type": "binary",
                "res_model": "uafe.report.wizard",
                "res_id": self.id,
            }
        )

        # Descargar el archivo
        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{attachment.id}?download=true",
            "target": "self",
        }


class UAFEReportWizardLine(models.TransientModel):
    _name = "uafe.report.wizard.line"
    _description = "Líneas del Reporte UAFE"

    wizard_id = fields.Many2one(
        "uafe.report.wizard", string="Wizard"
    )  # Relación con el wizard principal
    invoice_id = fields.Many2one("account.move", string="Factura")  # Factura vinculada
    partner_name = fields.Char(string="Cliente")
    invoice_date = fields.Date(string="Fecha de Factura")
    amount_total = fields.Float(string="Total")
