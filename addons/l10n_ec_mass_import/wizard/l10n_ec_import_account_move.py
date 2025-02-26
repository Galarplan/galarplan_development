# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from xlrd import open_workbook
from odoo.exceptions import ValidationError
import os
import tempfile
import xlsxwriter
import xlrd
from datetime import datetime, timedelta

class AccountMoveImportWizard(models.Model):
    _name = "account.move.import.wizard"
    _description = "Asistente para Importar Apuntes Contables"

    company_id = fields.Many2one(
        "res.company",
        string="Compañia",
        required=True,
        copy=False,
        default=lambda self: self.env.company,
    )

    file = fields.Binary("Archivo", required=True, filters='*.xlsx')
    file_name = fields.Char("Nombre de Archivo", required=False, size=255)

    diario = fields.Many2one('account.journal',string='Diario')    

    file_result = fields.Binary("Archivo Resultado", required=False, filters='*.xlsx')
    file_name_result = fields.Char("Nombre de Archivo Resultado", required=False, size=255)

    _rec_name = "id"
    _order = "id desc"

    def process(self):
        for brw_each in self:
            brw_each.process_file()
        return True

    def get_ext(self, file_name):
        return os.path.splitext(file_name)[1][1:]

    def create_file(self, ext):
        ext = f".{ext.lstrip('.')}"
        temp_file = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
        return temp_file.name

    def write_file(self, filename, str_data, modeWrite="wb"):
        import base64
        with open(filename, mode=modeWrite) as file:
            file.write(base64.b64decode(str_data))
        return str_data

    def guardar_mensajes(self, mensajes):
        import base64
        if not mensajes:
            return None
        import io
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()
        worksheet.write(0, 0, "Nombre")
        worksheet.write(0, 1, "Valores")
        worksheet.write(0, 2, "Mensaje")

        for row_idx, (nombre, valores, mensaje) in enumerate(mensajes, start=1):
            worksheet.write(row_idx, 0, nombre)
            worksheet.write(row_idx, 1, str(valores))
            worksheet.write(row_idx, 2, mensaje)

        workbook.close()
        output.seek(0)
        return base64.b64encode(output.read())

    def process_file(self):
        FECHA = 0
        NUMERO = 1
        EMPRESA = 2
        REFERENCIA = 3
        DIARIO = 4
        EMPRESA_2 = 5
        TOTAL_FIRMADO = 6
        ESTADO = 7
        CUENTA = 8
        EMPRESA_3 = 9
        ETIQUETA = 10
        DEBE = 11
        HABER = 12

        mensajes = []

        for brw_each in self:
            ext = self.get_ext(brw_each.file_name)
            fileName = self.create_file(ext)
            self.write_file(fileName, brw_each.file, modeWrite="wb")

            book = xlrd.open_workbook(fileName)
            sheet = book.sheet_by_index(0)

            # Crear un diario específico si no existe
            journal = self.env['account.journal'].search([('name', '=', 'Diario de Importación')], limit=1)
            if not journal:
                journal = self.env['account.journal'].create({
                    'name': 'Diario de Importación',
                    'code': 'IMP',
                    'type': 'general',
                    'company_id': brw_each.company_id.id,
                })

            # Variables para agrupar líneas por asiento contable
            current_move = None
            move_lines = []
            move_values = {}

            for row_index in range(1, sheet.nrows):
                try:
                    fecha = sheet.cell(row_index, FECHA).value
                    numero = sheet.cell(row_index, NUMERO).value
                    empresa = sheet.cell(row_index, EMPRESA).value
                    referencia = sheet.cell(row_index, REFERENCIA).value
                    diario = sheet.cell(row_index, DIARIO).value
                    empresa_2 = sheet.cell(row_index, EMPRESA_2).value
                    total_firmado = sheet.cell(row_index, TOTAL_FIRMADO).value
                    estado = sheet.cell(row_index, ESTADO).value
                    cuenta = sheet.cell(row_index, CUENTA).value
                    empresa_3 = sheet.cell(row_index, EMPRESA_3).value
                    etiqueta = sheet.cell(row_index, ETIQUETA).value
                    debe = sheet.cell(row_index, DEBE).value
                    haber = sheet.cell(row_index, HABER).value

                    # Si hay un número de asiento, es una nueva cabecera
                    if numero:
                        # Si hay un asiento previo, lo guardamos
                        if current_move:
                            move_values['line_ids'] = move_lines
                            move = self.env['account.move'].create(move_values)
                            mensajes.append((current_move, str(move.id), "ok"))
                            move_lines = []  # Reiniciar las líneas para el nuevo asiento

                        # Crear un nuevo asiento contable
                        current_move = numero
                        move_values = {
                            'date': fecha,
                            'ref': referencia,
                            'journal_id': journal.id,
                            'company_id': brw_each.company_id.id,
                        }

                    # Agregar la línea al asiento actual
                    account_id = self.env['account.account'].search([('code', '=', cuenta)], limit=1).id
                    if account_id:
                        move_lines.append((0, 0, {
                            'account_id': account_id,
                            'name': etiqueta,
                            'debit': debe,
                            'credit': haber,
                        }))

                except Exception as e:
                    error_msg = f"Error en fila {row_index}: {str(e)}"
                    mensajes.append(("Fila " + str(row_index), "", error_msg))

            # Guardar el último asiento contable
            if current_move and move_lines:
                move_values['line_ids'] = move_lines
                move = self.env['account.move'].create(move_values)
                mensajes.append((current_move, str(move.id), "ok"))

            archivo = self.guardar_mensajes(mensajes)
            self.write({
                "file_name_result": "mensajes.xlsx",
                "file_result": archivo
            })

            values = {
                'type': 'ir.actions.act_url',
                'url': '/web/content/%s/%s/file_result/%s' % (self._name, self.id, "mensajes.xlsx"),
                'target': 'new'
            }
            return values