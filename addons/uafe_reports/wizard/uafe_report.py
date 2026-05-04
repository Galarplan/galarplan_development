from odoo import models, fields, api
from datetime import datetime
import calendar
import base64
import io
import xlsxwriter
import pandas as pd
import unicodedata
import re


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

################################################
    def _clean_special_characters(self, text):
        """
        Limpia caracteres especiales:
        ñ -> n
        Ñ -> N
        áéíóú -> aeiou
        elimina símbolos raros
        reemplaza guiones por espacio
        """

        if not text:
            return ""

        text = str(text)

        # Reemplazos manuales importantes
        replacements = {
            "ñ": "n",
            "Ñ": "N",
            "-": " ",
            "_": " ",
            "/": " ",
            "\\": " ",
            "&": " ",
            "@": " ",
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        # Quitar tildes
        import unicodedata
        text = unicodedata.normalize("NFKD", text)
        text = text.encode("ASCII", "ignore").decode("utf-8")

        # Dejar solo letras, números y espacios
        import re
        text = re.sub(r"[^A-Za-z0-9\s]", "", text)

        # Quitar espacios múltiples
        text = re.sub(r"\s+", " ", text).strip()

        return text
################################################

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
                "C",
                "COD_TIPO_ID",
                "ID_CLIENTE",
                "NOMBRES_RAZON_SOCIAL",
                "APELLIDOS_NOMBRE_COMERCIAL",
                "COD_PAIS_NACIONALIDAD",
                "DIRECCION",
                "COD_PROVINCIA",
                "COD_CANTON",
                "COD_PARROQUIA",
                "ACTIVIDAD ECONOMICA (AEC)",
                "INGRESO_CLIENTE",
                "CÓDIGO REGISTRO (CDR)",                                            
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
                    'J' if partner.vat and partner.vat[-3:] == '001'
                        else 'N',
                    'R' if partner.l10n_latam_identification_type_id.name == 'RUC'
                        else 'C' if partner.l10n_latam_identification_type_id.name == 'Cédula'
                        else "",
                    partner.vat or "",
                    self._clean_special_characters(partner.name) or "",
                    partner.name or "",
                    partner.country_id.nationality_code or "",
                    self._clean_special_characters(partner.street) or "",
                    partner.state_id.code or "",
                    partner.country_substate_id.code or "",
                    partner.parish_id.code or "",
                    partner.economic_activity.code or "",
                    partner.monthly_income or "",
                    self.company_id.uafe_code,
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
                "COD_TIPO_ID",
                "ID_CLIENTE",
                "NUMERO_OPERACION",
                "COD_TIPO_ OPERACION",
                "TIPO_FINANCIAMIENTO",
                "VALOR_FINANCIAMIENTO_DIRECTO",
                "VALOR_FINANCIAMIENTO_EXTERNO",
                "VALOR_TOTAL_OPERACION",
                "FECHA_OPERACION",
                "ANIO_FABRICACION",
                "COD_TIPO_VEHICULO_MAQUINARIA",	
                "MODELO_VEHICULO_MAQUINARIA",
                "MARCA_VEHICULO_MAQUINARIA"	,
                "NUMERO_CHASIS_VEHICULO_MAQUINARIA",
                "CILINDRAJE_VEHICULO",
                "COD_NIVEL_BLINDAJE",
                "CONDICION_BIEN",
                "NUMERO_PLACA",
                "COD_PROV_OPERACION",
                "COD_CANTON_OPERACION",
                "COD_PARROQUIA_OPERACION",
            ]
        ]
        client_data = [
            [
                "OPR",
                self.company_id.uafe_code,
                fecha_corte,
                self.registro_number_operation,
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
            move = invoice.invoice_id
            partner = invoice.invoice_id.partner_id
            for line in invoice.invoice_id.invoice_line_ids:                
                product_id = line.product_id
                print('====================prdid',product_id)
                client_data.append(
                    [
                        'R' if partner.l10n_latam_identification_type_id.name == 'RUC'
                            else 'C' if partner.l10n_latam_identification_type_id.name == 'Cédula'
                            else "",
                        partner.vat or "",
                        ''.join(filter(str.isdigit, line.move_id.name or "")),
                        "COM",
                        'EXT' if move.is_galarplan or move.is_credit_bank
                            else 'NAP' if move.is_direct
                            else 'DIR' if move.is_credit_sale
                            else "",                        
                        move.direct_financing_value or 0.00,
                        move.external_financing_value or 0.00,
                        int(line.price_unit or 0),
                        move.invoice_date.strftime('%Y%m%d') if move.invoice_date else "",
                        product_id.model_year or "",
                        product_id.vehicle_type.name or "",
                        product_id.name or "",
                        product_id.vehicle_model_id.name or "",
                        product_id.chassis_number or "",
                        product_id.cylinder_capacity or "",
                        "NO",
                        "N" if (product_id.vehicle_status or "").lower() == "nuevo" 
                        else "U" if (product_id.vehicle_status or "").lower() == "usado" 
                        else "",
                        product_id.ramw_number or "",                        
                        "09",
                        "0901",
                        partner.parish_id.code or "",                                                
                    ]
                )
                print('=====================cld',client_data)
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
