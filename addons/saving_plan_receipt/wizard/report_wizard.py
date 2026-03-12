from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
import base64
from io import BytesIO
import xlsxwriter
from datetime import datetime

from odoo.addons.saving_plan_receipt.models.check_payment import PAYMENT_FORM, PAYMENT_REASON, STATE_RECEIPT

class ReportReceiptWz(models.TransientModel):
    _name = 'report.receipt.wz'
    _description = 'Wizard de Reporte de Pagos'

    date_from = fields.Date(
        string='Fecha Desde',
        required=True,
        default=fields.Date.context_today
    )
    date_to = fields.Date(
        string='Fecha Hasta',
        required=True,
        default=fields.Date.context_today
    )
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        default=lambda self: self.env.company,
        required=True
    )
    location_ids = fields.Many2many(
        'location.places',
        string='Ubicaciones',
        domain="[('company_id', '=', company_id)]"
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente'
    )
    
    filename = fields.Char(
        string='Nombre del Archivo',
        default='reporte_pagos.xlsx',
        readonly=True
    )
    file_data = fields.Binary(
        string='Archivo Excel',
        readonly=True
    )


    @staticmethod
    def get_payment_form(payment_form_list,value):
        for data in payment_form_list:
            if data[0] == value:
                return data[1]
            
    
    @staticmethod
    def get_payment_reason(payment_reason_list,value):
        for data in payment_reason_list:
            if data[0] == value:
                return data[1]
    

    @staticmethod
    def get_state_data(tuple_list,value):
        for data in tuple_list:
            if data[0] == value:
                return data[1]


    
    def action_generate_report(self):
        self.ensure_one()
        
        # Construir dominio para filtrar recibos
        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('company_id', '=', self.company_id.id)
        ]
        
        if self.location_ids:
            domain.append(('location_id', 'in', self.location_ids.ids))
            
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
            
        # Buscar recibos
        receipts = self.env['receipt.validation'].search(domain, order='date_payment asc, name asc')
        
        if not receipts:
            raise UserError(_('No hay recibos en el rango de fechas seleccionado.'))
        
        # Generar archivo Excel
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Reporte de Pagos')
        
        # Formatos
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4F81BD',
            'color': 'white',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })
        
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        subtitle_format = workbook.add_format({
            'bold': True,
            'font_size': 11,
            'align': 'left'
        })
        
        date_format = workbook.add_format({'num_format': 'dd-mmm-yyyy', 'align': 'left'})
        amount_format = workbook.add_format({'num_format': '#,##0.00', 'align': 'right'})
        text_format = workbook.add_format({'align': 'left'})
        center_format = workbook.add_format({'align': 'center'})
        
        # Fila inicial
        row = 0
        col = 0
        
        # Título de la compañía
        company_name = self.company_id.name or 'GALARPLAN S.A.'
        # worksheet.merge_range(row, col, row, col + len(headers) - 1, company_name, title_format)
        # row += 1
        
        total_columns = 24  # número real de columnas del reporte
        worksheet.merge_range(row, col, row, col + total_columns - 1, company_name, title_format)
        row += 1

        # Subtítulo del reporte
        worksheet.merge_range(row, col, row, col + total_columns - 1, 'REPORTE DE PAGOS', subtitle_format)
        row += 1
        
        # Rango de fechas
        date_range = f"Del {self.date_from.strftime('%d %B %Y')} al {self.date_to.strftime('%d %B %Y')}"
        worksheet.merge_range(row, col, row, col + total_columns - 1, date_range, subtitle_format)
        row += 2
        
        # Cabeceras de columnas
        headers = [
           'Fecha de Pago', 'Fecha de Recibo', '# Comp', 'Tipo Identificacion',
    'Identificacion Cliente', 'Nombre cliente',
    'Motivo del pago', 'Tipo pago', 'Valor pagado',
    'Billetes $50', 'Billetes $100',
    'Forma de pago', 'Tipo Tarjeta', 'Referencia de pago',
    '# Cuenta', 'Fecha del cheque', 'Banco Emisor', 'Banco Receptor',
    'Pago Tercero','Tercero ID','Tercero Nombre',
    'AGENCIA','CAJERO','ESTADO'
        ]
        
        for i, header in enumerate(headers):
            worksheet.write(row, i, header, header_format)
            worksheet.set_column(i, i, 18)  # Ancho de columna
        
        row += 1
        
        # Totales
        total_amount = 0
        
        # Llenar datos
        for receipt in receipts:
            col = 0
            
            # Fecha de Pago
            worksheet.write(row, col, receipt.date_payment, date_format)
            col += 1
            
            # Fecha de Recibo
            worksheet.write(row, col, receipt.date, date_format)
            col += 1
            
            # # Comp
            worksheet.write(row, col, receipt.name or '', text_format)
            col += 1
            
            # Tipo Identificacion
            id_type = ''
            if receipt.partner_id:
                id_type = 'R' if receipt.partner_id.company_type == 'company' else 'C'
            worksheet.write(row, col, id_type, center_format)
            col += 1
            
            # Identificacion Cliente
            worksheet.write(row, col, receipt.document_number or '', text_format)
            col += 1
            
            # Nombre cliente
            worksheet.write(row, col, receipt.partner_id.name or '', text_format)
            col += 1
            
            # Motivo del pago
            # payment_reason = self.get_state_data(PAYMENT_REASON,receipt.payment_reason) or ''
            payment_reason = receipt.payment_reason.name if receipt.payment_reason else ''
                
            worksheet.write(row, col, payment_reason, text_format)
            col += 1
            
            # Tipo pago
            payment_type = 'ANTICIPO DE CLIENTE'
            if receipt.saving_plan_payment:
                if receipt.saving_plan_id and receipt.saving_plan_id.state == 'adjudicated_with_assets':
                    payment_type = 'ADJ CON BIEN'
                else:
                    payment_type = 'PLAN AHORRO'
            worksheet.write(row, col, payment_type, text_format)
            col += 1
            
            # Valor pagado
            worksheet.write(row, col, receipt.amount, amount_format)
            total_amount += receipt.amount
            col += 1
            
            worksheet.write(row, col, receipt.val_cincuenta or 0, center_format)
            col += 1

            worksheet.write(row, col, receipt.val_cien or 0, center_format)
            col += 1

            # Forma de pago
            payment_form = self.get_state_data(PAYMENT_FORM,receipt.payment_form) or ''
            # payment_form = dict(receipt._fields['payment_form'].selection).get(receipt.payment_form, '')
            # if receipt.payment_form == 'other' and receipt.payment_other_desc:
            #     payment_form = receipt.payment_other_desc
            worksheet.write(row, col, payment_form, text_format)
            col += 1
            
            # Tipo Tarjeta
            card_type = ''
            if receipt.payment_form == 'card_credit':
                card_type = 'CR'
            elif receipt.payment_form == 'card_debit':
                card_type = 'DB'
            worksheet.write(row, col, card_type, center_format)
            col += 1
            
            # Referencia de pago
            reference = ''
            if receipt.payment_form == 'check':
                reference = receipt.number_check or ''
            elif receipt.payment_form in ['transfer', 'deposit']:
                reference = receipt.comp_number or ''
            elif receipt.payment_form in ['card_credit', 'card_debit']:
                reference = receipt.lote_card or ''
            worksheet.write(row, col, reference, text_format)
            col += 1
            
            # # Cuenta
            account = ''
            if receipt.payment_form == 'check':
                account = receipt.account_check or ''
            elif receipt.payment_form in ['transfer', 'deposit']:
                account = receipt.acc_number or ''
            elif receipt.payment_form in ['card_credit', 'card_debit']:
                account = receipt.card_number or ''
            worksheet.write(row, col, account, text_format)
            col += 1
            
            # Fecha del cheque
            if receipt.payment_form == 'check' and receipt.date_check:
                worksheet.write(row, col, receipt.date_check, date_format)
            else:
                worksheet.write(row, col, '', text_format)
            col += 1
            
            # Banco Emisor
            worksheet.write(row, col, receipt.banco_emisor.name if receipt.banco_emisor else '', text_format)
            col += 1
            
            # Banco Receptor
            worksheet.write(row, col, receipt.banco_receptor.name if receipt.banco_receptor else '', text_format)
            col += 1             

            pago_tercero = 'SI' if receipt.tercero else 'NO'
            worksheet.write(row, col, pago_tercero, center_format)
            col += 1

            worksheet.write(row, col, receipt.tercero_id or '', text_format)
            col += 1

            worksheet.write(row, col, receipt.tercero_name or '', text_format)
            col += 1            

            # AGENCIA (Ubicación)
            worksheet.write(row, col, receipt.location_id.name or '', text_format)
            col += 1
            
            # CAJERO (Usuario que imprime/crea)
            cashier = receipt.printed_by.name or receipt.asesor_id.name or receipt.create_uid.name or ''
            worksheet.write(row, col, cashier, text_format)
            col += 1

            receipt_state = self.get_state_data(STATE_RECEIPT,receipt.state)
            worksheet.write(row, col, receipt_state, text_format)
            col += 1                
            
            row += 1
        
        # Fila de totales
        row += 1
        worksheet.merge_range(row, 0, row, 7, 'TOTALES', header_format)
        worksheet.write(row, 8, total_amount, amount_format)
        last_col = len(headers) - 1
        worksheet.merge_range(row, 9, row, last_col, '', header_format)
        
        # Aplicar formato de moneda a la columna de valor pagado
        worksheet.set_column(8, 8, 15, amount_format)
        
        # Cerrar workbook
        workbook.close()
        
        # Convertir a base64
        output.seek(0)
        file_data = base64.b64encode(output.read())
        output.close()
        
        # Guardar en el wizard
        self.write({
            'filename': f'reporte_pagos_{self.date_from.strftime("%Y%m%d")}_{self.date_to.strftime("%Y%m%d")}.xlsx',
            'file_data': file_data
        })
        
        filename = f'reporte_pagos_{self.date_from.strftime("%Y%m%d")}_{self.date_to.strftime("%Y%m%d")}.xlsx'
    
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': file_data,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        
        # Generar URL de descarga
        download_url = f'/web/content/{attachment.id}?download=true'
        
        return {
            'type': 'ir.actions.act_url',
            'url': download_url,
            'target': 'self',
        }
        
        # Retornar acción para descargar
        # return {
        #     'name': 'Descargar Reporte',
        #     'type': 'ir.actions.act_url',
        #     'url': f'/web/content/{self.id}/{self.filename}?download=true',
        #     'target': 'self',
        # }