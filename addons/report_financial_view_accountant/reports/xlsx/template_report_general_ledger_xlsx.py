from odoo import fields, models, tools, _
import operator
from itertools import groupby
from datetime import datetime
from io import BytesIO


class grl_ledger_xlsx(models.AbstractModel):
    _name = 'report.report_financial_view_accountant.grl_ledger_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = _("Reporte Mayor personalizado")

    def generate_xlsx_report(self, workbook, data, tradename):
        workbook.formats[0].set_font_size(9)

        # Configuración del worksheet
        worksheet = workbook.add_worksheet(name="RMC")
        worksheet.set_portrait()
        worksheet.center_horizontally()
        worksheet.set_paper(9)
        worksheet.set_margins(left=0.125, right=0.125, top=0.15, bottom=0.15)
        worksheet.freeze_panes(4, 0)

        for obj in tradename:
            context = dict(self._context)
            dictionary_parameter = obj.pre_print_reportfile()
            res = obj.action_process_sql()
            # Formatos de celdas

            f_string_title_left = workbook.add_format({
                'num_format': '@',
                'bold': True,
                'font_size': 14,
                'valign': 'top',
                'align': 'left',
            })
            f_string_title_center = workbook.add_format({
                'num_format': '@',
                'bold': True,
                'font_size': 14,
                'valign': 'top',
                'align': 'center',
            })
            f_string_subtitle_left = workbook.add_format({
                'num_format': '@',
                'bold': True,
                'font_size': 10,
                'valign': 'top',
                'align': 'left',
            })
            f_string_subtitle_center = workbook.add_format({
                'num_format': '@',
                'bold': True,
                'font_size': 10,
                'valign': 'top',
                'align': 'center',
            })
            f_string_plain_left = workbook.add_format({
                'num_format': '@',
                'font_size': 9,
                'valign': 'top',
                'align': 'left',
            })
            f_string_plain_center = workbook.add_format({
                'num_format': '@',
                'font_size': 9,
                'valign': 'top',
                'align': 'center',
            })
            f_string_plain_right = workbook.add_format({
                'num_format': '@',
                'font_size': 9,
                'valign': 'top',
                'align': 'right',
            })
            f_string_bold_left = workbook.add_format({
                'num_format': '@',
                'bold': True,
                'font_size': 9,
                'valign': 'top',
                'align': 'left',
            })
            f_string_bold_right = workbook.add_format({
                'num_format': '@',
                'bold': True,
                'font_size': 9,
                'valign': 'top',
                'align': 'right',
            })
            f_string_bold_header_left = workbook.add_format({
                'num_format': '@',
                'bold': True,
                'font_size': 9,
                'valign': 'top',
                'align': 'center',
                'text_wrap': True,
                'top': 1,
                'bottom': 1,
                'font_color': 'white',  # Color del texto
                'bg_color': '#AF2B2F',  # Color de fondo
            })
            f_string_bold_header_cl1_left = workbook.add_format({
                'num_format': '@',
                'bold': True,
                'font_size': 9,
                'valign': 'top',
                'align': 'center',
                'text_wrap': True,
                'top': 1,
                'bottom': 1,
                'font_color': 'white',  # Color del texto
                'bg_color': '#A3A3A3',  # Color de fondo
            })
            f_date = workbook.add_format({
                'num_format': 'dd/mm/yyyy',
                'font_size': 9,
                'valign': 'top',
            })
            f_integer = workbook.add_format({
                'num_format': '0',
                'font_size': 9,
                'valign': 'top',
            })
            f_float_2d = workbook.add_format({
                'num_format': '0.00',
                'font_size': 9,
                'valign': 'top',
            })
            f_percentage = workbook.add_format({
                'num_format': '#,##0.00%',
                'font_size': 9,
                'valign': 'top',
            })

            # Ancho de columnas
            worksheet.set_column(0, 0, 10)  #
            worksheet.set_column(1, 1, 40)  #
            worksheet.set_column(2, 2, 30)  #
            worksheet.set_column(3, 3, 30)  #
            worksheet.set_column(4, 4, 40)  #
            worksheet.set_column(5, 5, 15)  #
            worksheet.set_column(6, 6, 20)  #
            worksheet.set_column(7, 7, 20)  #
            worksheet.set_column(8, 8, 10)  #
            worksheet.set_column(9, 9, 30)  #
            worksheet.set_column(10, 10, 10)  #
            worksheet.set_column(11, 11, 10)  #
            worksheet.set_column(12, 12, 30)  #
            worksheet.set_column(13, 13, 20)  #
            worksheet.set_column(14, 14, 20)  #
            worksheet.set_column(15, 15, 10)  #
            worksheet.set_column(16, 16, 10)  #
            worksheet.set_column(17, 17, 10)  #
            worksheet.set_column(18, 18, 10)  #
            worksheet.set_column(19, 19, 10)  #

            # Información de cabecera
            # start_date = datetime.strptime(dictionary_parameter['date_start'], "%Y-%m-%d").strftime("%d/%m/%Y")
            # end_date = datetime.strptime(dictionary_parameter['date_end'], "%Y-%m-%d").strftime("%d/%m/%Y")
            # worksheet.write(0, 0, 'REPORTE DE MAYOR PERSONALIZADO', f_string_title_left)
            # with open(obj.company_id.logo, "rb") as f:
            #     imagen_binaria = f.read()
            # imagen_stream = BytesIO(imagen_binaria)
            # worksheet.insert_image('B2', 'imagen_virtual.png', {'image_data': obj.company_id.logo})

            worksheet.merge_range(1, 12, 1, 14, obj.company_id.name, f_string_title_center)
            worksheet.merge_range(2, 4, 2, 10, 'REPORTE MAYOR', f_string_title_center)
            worksheet.merge_range(3, 4, 3, 10, (obj.date_from and str(obj.date_from) or '') + ' al ' + (obj.date_to and str(obj.date_to) or ''),
                                  f_string_title_center)
            
            account_code = str(obj.account_id.code) if obj.account_id.code else ""
            account_name = str(obj.account_id.name) if obj.account_id.name else ""
            account_display = f"{account_code} {account_name}".strip()
            
            worksheet.merge_range(4, 4, 4, 10, account_display, f_string_title_center)
            # worksheet.write(1, 0, 'DESDE: %s - HASTA: %s' % (start_date, end_date), f_string_subtitle_left)

            # Diccionario de cabeceras
            headers = {
                0: "FECHA",
                1: "CUENTA CONTABLE",
                2: "NOMBRE",
                3: "SOCIO",
                4: "REFERENCIA",
                5: "MOVIMIENTO",
                6: "CENTRO",
                7: "USUARIO",
                8: "MONEDA",
                9: "PRODUCTO",
                10: "CANTIDAD",
                11: "UDM",
                12: "DIARIO CONTABLE",
                13: "PAGO",
                14: "CUENTA ANALÍTICA",
                15: "DÉBITO",
                16: "CRÉDITO",
                17: "TOTAL DÉBITO",
                18: "TOTAL CRÉDITO",
                19: "TOTAL ACUMULADO"
            }
            col_pos = 0
            row_pos = 9
            #
            res_list_init = obj.action_process_init_sql(None, obj.date_from)
            res_init = res_list_init and res_list_init[0]['balance'] or 0
            #
            worksheet.write(row_pos - 1, 0, '', f_string_bold_header_cl1_left)
            worksheet.write(row_pos - 1, 1, '', f_string_bold_header_cl1_left)
            worksheet.write(row_pos - 1, 2, '', f_string_bold_header_cl1_left)
            worksheet.write(row_pos - 1, 3, '', f_string_bold_header_cl1_left)
            worksheet.write(row_pos - 1, 4, '', f_string_bold_header_cl1_left)
            worksheet.write(row_pos - 1, 5, '', f_string_bold_header_cl1_left)
            worksheet.write(row_pos - 1, 6, '', f_string_bold_header_cl1_left)
            worksheet.write(row_pos - 1, 7, '', f_string_bold_header_cl1_left)
            worksheet.write(row_pos - 1, 8, '', f_string_bold_header_cl1_left)
            worksheet.write(row_pos - 1, 9, '', f_string_bold_header_cl1_left)
            worksheet.write(row_pos - 1, 10, '', f_string_bold_header_cl1_left)
            worksheet.write(row_pos - 1, 11, 'SALDO INICIAL', f_string_bold_header_cl1_left)
            worksheet.write(row_pos - 1, 12, '', f_string_bold_header_cl1_left)
            worksheet.write(row_pos - 1, 13, '', f_string_bold_header_cl1_left)
            worksheet.write(row_pos - 1, 14, '', f_string_bold_header_cl1_left)
            worksheet.write(row_pos - 1, 15, '', f_string_bold_header_cl1_left)
            worksheet.write(row_pos - 1, 16, '', f_string_bold_header_cl1_left)
            worksheet.write(row_pos - 1, 17, '', f_string_bold_header_cl1_left)
            worksheet.write(row_pos - 1, 18, '', f_string_bold_header_cl1_left)
            worksheet.write(row_pos - 1, 19, res_init, f_string_bold_header_cl1_left)
            row_pos += 1
            #
            worksheet.autofilter(row_pos, 0, row_pos, len(headers) - 1)
            for each_lst in headers.keys():
                worksheet.write(row_pos, each_lst, headers.get(each_lst), f_string_bold_header_left)
            row_pos += 2
            ############################################################
            sum_debit = 0
            sum_credit = 0
            amount_balance = res_init
            for move in res:
                sum_debit += move.get('debit')
                sum_credit += move.get('credit')
                amount_balance += move.get('balance', 0)
                brw_move_line = self.env['account.move.line'].browse(move.get('move_line_id'))
                worksheet.write(row_pos, 0, move.get('ldate'), f_date)
                worksheet.write(row_pos, 1, brw_move_line.account_id.code + ' ' + brw_move_line.account_id.name, f_string_plain_left)
                worksheet.write(row_pos, 2, move.get('lname'), f_string_plain_left)
                worksheet.write(row_pos, 3, brw_move_line.partner_id.name, f_string_plain_left)
                worksheet.write(row_pos, 4, move.get('referencia', ''), f_string_plain_left)
                worksheet.write(row_pos, 5, '', f_string_plain_left)
                worksheet.write(row_pos, 6, '', f_string_plain_left)
                worksheet.write(row_pos, 7, brw_move_line.create_uid.name, f_string_plain_left)
                worksheet.write(row_pos, 8, brw_move_line.currency_id.name, f_string_plain_left)
                worksheet.write(row_pos, 9, brw_move_line.product_id.name, f_string_plain_left)
                worksheet.write(row_pos, 10, brw_move_line.quantity, f_float_2d)
                worksheet.write(row_pos, 11, 0, f_float_2d)
                worksheet.write(row_pos, 12, brw_move_line.journal_id.name, f_float_2d)
                worksheet.write(row_pos, 13, (brw_move_line.payment_id and brw_move_line.payment_id.name or ''), f_string_plain_left)
                worksheet.write(row_pos, 14, '', f_string_plain_left)
                worksheet.write(row_pos, 15, move.get('debit'), f_float_2d)
                worksheet.write(row_pos, 16, move.get('credit'), f_float_2d)
                worksheet.write(row_pos, 17, sum_debit, f_float_2d)
                worksheet.write(row_pos, 18, sum_credit, f_float_2d)
                worksheet.write(row_pos, 19, amount_balance, f_float_2d)
                row_pos += 1
            # FILA DE 1ERA SUMATORIA
            row_pos += 1
            worksheet.write(row_pos, 0, 'SUBTOTAL', f_string_bold_header_left)
            account_code = str(obj.account_id.code) if obj.account_id.code else ""
            account_name = str(obj.account_id.name) if obj.account_id.name else ""
            account_display = f"{account_code} {account_name}".strip()

            worksheet.write(row_pos, 1, account_display, f_string_bold_header_left)
            worksheet.write(row_pos, 2, '', f_string_bold_header_left)
            worksheet.write(row_pos, 3, '', f_string_bold_header_left)
            worksheet.write(row_pos, 4, '', f_string_bold_header_left)
            worksheet.write(row_pos, 5, '', f_string_bold_header_left)
            worksheet.write(row_pos, 6, '', f_string_bold_header_left)
            worksheet.write(row_pos, 7, '', f_string_bold_header_left)
            worksheet.write(row_pos, 8, '', f_string_bold_header_left)
            worksheet.write(row_pos, 9, '', f_string_bold_header_left)
            worksheet.write(row_pos, 10, '', f_string_bold_header_left)
            worksheet.write(row_pos, 11, '', f_string_bold_header_left)
            worksheet.write(row_pos, 12, '', f_string_bold_header_left)
            worksheet.write(row_pos, 13, '', f_string_bold_header_left)
            worksheet.write(row_pos, 14, '', f_string_bold_header_left)
            worksheet.write(row_pos, 15, sum_debit, f_string_bold_header_left)
            worksheet.write(row_pos, 16, sum_credit, f_string_bold_header_left)
            worksheet.write(row_pos, 17, '', f_string_bold_header_left)
            worksheet.write(row_pos, 18, '', f_string_bold_header_left)
            worksheet.write(row_pos, 19, '', f_string_bold_header_left)
            # FILA DE 2DA SUMATORIA
            row_pos += 2
            worksheet.write(row_pos, 0, '', f_string_bold_header_cl1_left)
            worksheet.write(row_pos, 1, '', f_string_bold_header_cl1_left)
            worksheet.write(row_pos, 2, '', f_string_bold_header_cl1_left)
            worksheet.write(row_pos, 3, '', f_string_bold_header_cl1_left)
            worksheet.write(row_pos, 4, '', f_string_bold_header_cl1_left)
            worksheet.write(row_pos, 5, '', f_string_bold_header_cl1_left)
            worksheet.write(row_pos, 6, '', f_string_bold_header_cl1_left)
            worksheet.write(row_pos, 7, '', f_string_bold_header_cl1_left)
            worksheet.write(row_pos, 8, '', f_string_bold_header_cl1_left)
            worksheet.write(row_pos, 9, '', f_string_bold_header_cl1_left)
            worksheet.write(row_pos, 10, '', f_string_bold_header_cl1_left)
            worksheet.write(row_pos, 11, 'SALDO FINAL', f_string_bold_header_cl1_left)
            worksheet.write(row_pos, 12, '', f_string_bold_header_cl1_left)
            worksheet.write(row_pos, 13, '', f_string_bold_header_cl1_left)
            worksheet.write(row_pos, 14, '', f_string_bold_header_cl1_left)
            worksheet.write(row_pos, 15, '', f_string_bold_header_cl1_left)
            worksheet.write(row_pos, 16, '', f_string_bold_header_cl1_left)
            worksheet.write(row_pos, 17, '', f_string_bold_header_cl1_left)
            worksheet.write(row_pos, 18, '', f_string_bold_header_cl1_left)
            worksheet.write(row_pos, 19, amount_balance, f_string_bold_header_cl1_left)
            return obj
