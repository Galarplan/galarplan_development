# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import logging
import io
import base64
import xlsxwriter
from odoo.tools import date_utils

_logger = logging.getLogger(__name__)


class SavingAgingWizard(models.TransientModel):
    _name = 'saving.aging.wizard'
    _description = 'Wizard para Reporte de Antigüedad de Cuotas de Ahorro'

    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company
    )
    
    report_date = fields.Date(
        string='Fecha de Corte',
        required=True,
        default=fields.Date.today
    )
    
    partner_ids = fields.Many2many(
        'res.partner',
        string='Socios (Filtrar)',
        help='Dejar vacío para incluir todos los socios'
    )
    
    saving_plan_ids = fields.Many2many(
        'account.saving',
        string='Planes de Ahorro (Filtrar)',
        help='Dejar vacío para incluir todos los planes'
    )
    
    state_plan_filter = fields.Selection([
        ('all', 'Todos'),
        ('posted', 'Confirmados'),
        ('active', 'Activos'),
        ('adjudicated_with_assets', 'Adjudicados con Bien'),
        ('adjudicated_without_assets', 'Adjudicados sin Bien'),
        ('awarded', 'Adjudicados'),
        ('estructured', 'Estructurados'),
        ('moved', 'Movidos'),
    ], string='Estado del Plan', default='all')
    
    show_zero_balance = fields.Boolean(
        string='Mostrar saldo cero',
        default=False,
        help='Mostrar planes con saldo pendiente igual a cero'
    )
    
    show_paid_lines = fields.Boolean(
        string='Mostrar cuotas pagadas',
        default=False,
        help='Mostrar líneas de cuotas que ya están pagadas'
    )
    
    output_format = fields.Selection([
        ('pdf', 'PDF'),
        ('xlsx', 'Excel'),
    ], string='Formato de Salida', default='xlsx')
    
    xlsx_file = fields.Binary(
        string='Archivo Excel',
        attachment=True
    )
    
    xlsx_filename = fields.Char(
        string='Nombre del Archivo Excel',
        default='Reporte_Antiguedad_Cuotas.xlsx'
    )

    def action_generate_report(self):
        """Genera el reporte según el formato seleccionado"""
        self.ensure_one()
        
        if self.output_format == 'xlsx':
            return self._export_xlsx()
        else:
            return self._export_pdf()
    
    def _export_pdf(self):
        """Exporta el reporte en formato PDF"""
        return self.env.ref('account_saving_aging_report.action_report_saving_aging').report_action(self)
    
    def _export_xlsx(self):
        """Exporta el reporte en formato Excel"""
        # Obtener datos del reporte
        report_data = self.get_report_data()
        
        if not report_data.get('data'):
            raise ValidationError(_('No hay datos para exportar con los filtros seleccionados.'))
        
        # Crear el archivo Excel en memoria
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        # Formatos
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#2c3e50',
            'color': 'white',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'font_size': 10,
        })
        
        subheader_format = workbook.add_format({
            'bold': True,
            'bg_color': '#34495e',
            'color': 'white',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'font_size': 9,
        })
        
        money_format = workbook.add_format({
            'num_format': '#,##0.00',
            'align': 'right',
            'valign': 'vcenter',
            'border': 1,
            'font_size': 9,
        })
        
        money_bold_format = workbook.add_format({
            'num_format': '#,##0.00',
            'align': 'right',
            'valign': 'vcenter',
            'border': 1,
            'bold': True,
            'font_size': 9,
        })
        
        text_format = workbook.add_format({
            'align': 'left',
            'valign': 'vcenter',
            'border': 1,
            'font_size': 9,
        })
        
        text_center_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'font_size': 9,
        })
        
        total_format = workbook.add_format({
            'bold': True,
            'bg_color': '#ecf0f1',
            'align': 'right',
            'valign': 'vcenter',
            'border': 1,
            'font_size': 9,
            'num_format': '#,##0.00',
        })
        
        total_text_format = workbook.add_format({
            'bold': True,
            'bg_color': '#ecf0f1',
            'align': 'right',
            'valign': 'vcenter',
            'border': 1,
            'font_size': 9,
        })
        
        # HOJA 1: Resumen por Socio
        sheet1 = workbook.add_worksheet('Resumen')
        sheet1.set_column('A:A', 30)  # Socio
        sheet1.set_column('B:B', 15)  # RUC/CI
        sheet1.set_column('C:C', 8)   # Planes
        sheet1.set_column('D:D', 14)  # Total Deuda
        sheet1.set_column('E:E', 14)  # Por Vencer (no se usa en este query)
        sheet1.set_column('F:F', 14)  # 1-30 d.
        sheet1.set_column('G:G', 14)  # 31-60 d.
        sheet1.set_column('H:H', 14)  # 61-90 d.
        sheet1.set_column('I:I', 14)  # 91-120 d.
        sheet1.set_column('J:J', 14)  # +120 d.
        
        row = 0
        
        # Título
        sheet1.merge_range(row, 0, row, 9, 'REPORTE DE ANTIGÜEDAD DE CUOTAS POR COBRAR', header_format)
        row += 1
        sheet1.merge_range(row, 0, row, 9, 'Planes de Ahorro', subheader_format)
        row += 2
        
        # Información del reporte
        sheet1.write(row, 0, 'Compañía:', text_format)
        sheet1.write(row, 1, self.company_id.name, text_format)
        sheet1.write(row, 5, 'Fecha de Corte:', text_format)
        sheet1.write(row, 6, self.report_date.strftime('%d/%m/%Y'), text_format)
        row += 1
        sheet1.write(row, 0, 'Fecha de Generación:', text_format)
        sheet1.write(row, 1, fields.Date.today().strftime('%d/%m/%Y'), text_format)
        sheet1.write(row, 5, 'Total de Planes:', text_format)
        sheet1.write(row, 6, len(report_data['data']), text_format)
        row += 2
        
        # Cabecera del Resumen por Socio
        headers = ['Socio', 'RUC/CI', 'Planes', 'Total Deuda', '1-30 d.', '31-60 d.', '61-90 d.', '91-120 d.', '+120 d.', 'Cuotas Vencidas']
        for col, header in enumerate(headers):
            sheet1.write(row, col, header, subheader_format)
        row += 1
        
        # Datos del Resumen por Socio
        partner_summary = {}
        for item in report_data['data']:
            partner_id = item['partner_id']
            if partner_id not in partner_summary:
                partner_summary[partner_id] = {
                    'partner_name': item['partner_name'],
                    'partner_vat': item['partner_vat'],
                    'plans': [],
                    'total_due': 0.0,
                    'total_age_30': 0.0,
                    'total_age_60': 0.0,
                    'total_age_90': 0.0,
                    'total_age_120': 0.0,
                    'total_age_older': 0.0,
                    'total_quota_count': 0,
                }
            partner_summary[partner_id]['plans'].append(item)
            partner_summary[partner_id]['total_due'] += item['total_due']
            partner_summary[partner_id]['total_age_30'] += item['total_age_30']
            partner_summary[partner_id]['total_age_60'] += item['total_age_60']
            partner_summary[partner_id]['total_age_90'] += item['total_age_90']
            partner_summary[partner_id]['total_age_120'] += item['total_age_120']
            partner_summary[partner_id]['total_age_older'] += item['total_age_older']
            partner_summary[partner_id]['total_quota_count'] += item['overdue_quota_count']
        
        for partner_data in partner_summary.values():
            sheet1.write(row, 0, partner_data['partner_name'], text_format)
            sheet1.write(row, 1, partner_data['partner_vat'], text_format)
            sheet1.write(row, 2, len(partner_data['plans']), text_center_format)
            sheet1.write(row, 3, partner_data['total_due'], money_format)
            sheet1.write(row, 4, partner_data['total_age_30'], money_format)
            sheet1.write(row, 5, partner_data['total_age_60'], money_format)
            sheet1.write(row, 6, partner_data['total_age_90'], money_format)
            sheet1.write(row, 7, partner_data['total_age_120'], money_format)
            sheet1.write(row, 8, partner_data['total_age_older'], money_format)
            sheet1.write(row, 9, partner_data['total_quota_count'], text_center_format)
            row += 1
        
        # Totales
        totals = report_data['totals']
        sheet1.write(row, 2, 'TOTALES', total_text_format)
        sheet1.write(row, 3, totals['total_due'], total_format)
        sheet1.write(row, 4, totals['total_age_30'], total_format)
        sheet1.write(row, 5, totals['total_age_60'], total_format)
        sheet1.write(row, 6, totals['total_age_90'], total_format)
        sheet1.write(row, 7, totals['total_age_120'], total_format)
        sheet1.write(row, 8, totals['total_age_older'], total_format)
        sheet1.write(row, 9, totals['total_quota_count'], total_text_format)
        
        # HOJA 2: Detalle de Cuotas por Plan
        sheet2 = workbook.add_worksheet('Detalle de Cuotas')
        sheet2.set_column('A:A', 15)  # Plan
        sheet2.set_column('B:B', 30)  # Socio
        sheet2.set_column('C:C', 12)  # Estado
        sheet2.set_column('D:D', 8)   # #
        sheet2.set_column('E:E', 12)  # Fecha
        sheet2.set_column('F:F', 10)  # Días Venc.
        sheet2.set_column('G:G', 12)  # Estado Pago
        sheet2.set_column('H:H', 14)  # Total
        sheet2.set_column('I:I', 14)  # Pagado
        sheet2.set_column('J:J', 14)  # Pendiente
        sheet2.set_column('K:K', 14)  # 1-30 d.
        sheet2.set_column('L:L', 14)  # 31-60 d.
        sheet2.set_column('M:M', 14)  # 61-90 d.
        sheet2.set_column('N:N', 14)  # 91-120 d.
        sheet2.set_column('O:O', 14)  # +120 d.
        
        row = 0
        
        # Título
        sheet2.merge_range(row, 0, row, 14, 'DETALLE DE CUOTAS POR PLAN', header_format)
        row += 2
        
        # Cabecera de Detalle
        detail_headers = ['Plan', 'Socio', 'Estado', '#', 'Fecha', 'Días Venc.', 'Estado Pago', 'Total', 'Pagado', 'Pendiente', 
                         '1-30 d.', '31-60 d.', '61-90 d.', '91-120 d.', '+120 d.']
        for col, header in enumerate(detail_headers):
            sheet2.write(row, col, header, subheader_format)
        row += 1
        
        # Datos de Detalle
        for plan in report_data['data']:
            # Mostrar todas las líneas si show_paid_lines está activado
            # o solo líneas con amount_residual > 0
            for line in plan['lines']:
                amount_residual = line.get('amount_residual') or 0
                if self.show_paid_lines or amount_residual > 0:
                    sheet2.write(row, 0, plan['saving_name'], text_format)
                    sheet2.write(row, 1, plan['partner_name'], text_format)
                    sheet2.write(row, 2, plan['state_plan_description'], text_format)
                    sheet2.write(row, 3, line['quota_number'], text_center_format)
                    sheet2.write(row, 4, line['quota_date'].strftime('%d/%m/%Y') if line['quota_date'] else '', text_center_format)
                    sheet2.write(row, 5, line['days_overdue'] if line['days_overdue'] > 0 else 0, text_center_format)
                    
                    # Estado de pago
                    estado_pago = line.get('estado_pago', '')
                    estado_pago_desc = {
                        'pendiente': 'Pendiente',
                        'sin_aplicar': 'Sin Aplicar',
                        'pagado': 'Pagado',
                        'cancelado': 'Cancelado'
                    }.get(estado_pago, estado_pago)
                    sheet2.write(row, 6, estado_pago_desc, text_center_format)
                    
                    sheet2.write(row, 7, line['amount_total'], money_format)
                    sheet2.write(row, 8, line['amount_paid'], money_format)
                    sheet2.write(row, 9, line['amount_residual'], money_bold_format)
                    sheet2.write(row, 10, line['age_30'], money_format)
                    sheet2.write(row, 11, line['age_60'], money_format)
                    sheet2.write(row, 12, line['age_90'], money_format)
                    sheet2.write(row, 13, line['age_120'], money_format)
                    sheet2.write(row, 14, line['age_older'], money_format)
                    row += 1
            
            # Totales del plan
            sheet2.write(row, 6, 'TOTAL PLAN:', total_text_format)
            sheet2.write(row, 9, plan['total_due'], total_format)
            sheet2.write(row, 10, plan['total_age_30'], total_format)
            sheet2.write(row, 11, plan['total_age_60'], total_format)
            sheet2.write(row, 12, plan['total_age_90'], total_format)
            sheet2.write(row, 13, plan['total_age_120'], total_format)
            sheet2.write(row, 14, plan['total_age_older'], total_format)
            row += 1
            
            # Información de cuotas vencidas
            sheet2.write(row, 6, 'Cuotas Vencidas:', total_text_format)
            sheet2.write(row, 9, plan['overdue_quota_count'], text_center_format)
            row += 1
            
            # Fila en blanco entre planes
            row += 1
        
        workbook.close()
        output.seek(0)
        
        # Guardar el archivo
        xlsx_data = base64.b64encode(output.getvalue())
        
        filename = f"Reporte_Antiguedad_Cuotas_{fields.Date.today().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        # Crear el attachment
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': xlsx_data,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'res_model': self._name,
            'res_id': self.id,
        })
        
        # Abrir el attachment para descarga
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }
    
    def get_report_data_sql(self):
        """
        Versión SQL optimizada con arrays - basada en el query original
        """
        report_date = self.report_date
        company_id = self.company_id.id
        
        # Fecha de reporte como string para usar en f-string
        report_date_str = report_date.strftime('%Y-%m-%d')
        
        # Construir filtros dinámicos
        # filters = []
        # params = []
        
        partner_id_clause = ""
        saving_id_clause = ""
        state_plan_clause = ""

        if self.partner_ids and self.partner_ids.ids:
            # Convertir a tupla y manejar caso de un solo elemento
            ids_tuple = tuple(self.partner_ids.ids)
            if len(ids_tuple) == 1:
                partner_id_clause = f"AND as1.partner_id = {ids_tuple[0]}"
            else:
                partner_id_clause = f"AND as1.partner_id IN {ids_tuple}"
        
        if self.saving_plan_ids and self.saving_plan_ids.ids:
            ids_tuple = tuple(self.saving_plan_ids.ids)
            if len(ids_tuple) == 1:
                saving_id_clause = f"AND as1.id = {ids_tuple[0]}"
            else:
                saving_id_clause = f"AND as1.id IN {ids_tuple}"
            
        if self.state_plan_filter != 'all':            
            state_plan_clause = f"AND  as1.state_plan = '{self.state_plan_filter}'"

        
        # Filtro para mostrar/ocultar líneas pagadas
        paid_lines_filter = ""
        if not self.show_paid_lines:
            paid_lines_filter = "AND asl.estado_pago IN ('pendiente', 'sin_aplicar')"
        
        # Query con la estructura exacta del query original
        query = f"""
        WITH saving_lines_data AS (
            SELECT DISTINCT ON (asl.id)
                as1.id AS saving_id,
                as1.name AS saving_name,
                as1.state_plan,
                as1.partner_id,
                rp.name AS partner_name,
                rp.vat AS partner_vat,
                asl.id AS line_id,
                asl.number AS quota_number,
                asl.date AS quota_date,
                asl.principal_amount,
                asl.serv_admin_amount,
                asl.seguro_amount,
                asl.serv_inscription_amount,
                asl.por_pagar AS amount_total,
                asl.pagos AS amount_paid,
                asl.pendiente AS amount_residual,
                asl.estado_pago,
                asl.invoice_id,
                am.name AS invoice_name,
                rc.currency_id,
                -- Días de vencimiento
                ('{report_date_str}'::date - asl.date) AS days_overdue,
                -- Clasificación por días de vencimiento
                CASE 
                    WHEN asl.pendiente = 0 OR asl.pendiente IS NULL THEN 0
                    WHEN asl.date <= '{report_date_str}'::date THEN asl.pendiente 
                    ELSE 0 
                END AS amount_due,
                CASE 
                    WHEN asl.pendiente = 0 OR asl.pendiente IS NULL THEN 0
                    WHEN asl.date > '{report_date_str}'::date THEN asl.pendiente 
                    ELSE 0 
                END AS age_not_due,
                CASE 
                    WHEN asl.pendiente = 0 OR asl.pendiente IS NULL THEN 0
                    WHEN asl.date <= '{report_date_str}'::date 
                        AND ('{report_date_str}'::date - asl.date) BETWEEN 0 AND 30 THEN asl.pendiente 
                    ELSE 0 
                END AS age_30,
                CASE 
                    WHEN asl.pendiente = 0 OR asl.pendiente IS NULL THEN 0
                    WHEN asl.date <= '{report_date_str}'::date 
                        AND ('{report_date_str}'::date - asl.date) BETWEEN 31 AND 60 THEN asl.pendiente 
                    ELSE 0 
                END AS age_60,
                CASE 
                    WHEN asl.pendiente = 0 OR asl.pendiente IS NULL THEN 0
                    WHEN asl.date <= '{report_date_str}'::date 
                        AND ('{report_date_str}'::date - asl.date) BETWEEN 61 AND 90 THEN asl.pendiente 
                    ELSE 0 
                END AS age_90,
                CASE 
                    WHEN asl.pendiente = 0 OR asl.pendiente IS NULL THEN 0
                    WHEN asl.date <= '{report_date_str}'::date 
                        AND ('{report_date_str}'::date - asl.date) BETWEEN 91 AND 120 THEN asl.pendiente 
                    ELSE 0 
                END AS age_120,
                CASE 
                    WHEN asl.pendiente = 0 OR asl.pendiente IS NULL THEN 0
                    WHEN asl.date <= '{report_date_str}'::date 
                        AND ('{report_date_str}'::date - asl.date) > 120 THEN asl.pendiente 
                    ELSE 0 
                END AS age_older
            FROM account_saving as1
            INNER JOIN res_partner rp ON rp.id = as1.partner_id
            INNER JOIN account_saving_lines asl ON asl.saving_id = as1.id
            LEFT JOIN account_move am ON am.id = asl.invoice_id
            JOIN res_company rc ON as1.company_id = rc.id
            WHERE as1.state_plan IN ('posted','active', 'adjudicated_with_assets','adjudicated_without_assets','awarded','estructured','moved')
                AND as1.company_id = {company_id}
                AND asl.date <= '{report_date_str}'::date
                {partner_id_clause}
                {saving_id_clause}
                {state_plan_clause}
                {paid_lines_filter}
            ORDER BY asl.id
        )
        SELECT 
            saving_id,
            saving_name,
            partner_id,
            partner_name,
            partner_vat,
            state_plan,
            array_agg(line_id ORDER BY quota_number ASC) AS line_ids,
            array_agg(quota_number ORDER BY quota_number ASC) AS quota_numbers,
            array_agg(quota_date ORDER BY quota_number ASC) AS quota_dates,
            array_agg(amount_total ORDER BY quota_number ASC) AS amount_totals,
            array_agg(amount_paid ORDER BY quota_number ASC) AS amount_paids,
            array_agg(amount_residual ORDER BY quota_number ASC) AS amount_residuals,
            array_agg(days_overdue ORDER BY quota_number ASC) AS days_overdues,
            array_agg(age_30 ORDER BY quota_number ASC) AS ages_30,
            array_agg(age_60 ORDER BY quota_number ASC) AS ages_60,
            array_agg(age_90 ORDER BY quota_number ASC) AS ages_90,
            array_agg(age_120 ORDER BY quota_number ASC) AS ages_120,
            array_agg(age_older ORDER BY quota_number ASC) AS ages_older,
            array_agg(estado_pago ORDER BY quota_number ASC) AS payment_states,
            array_agg(invoice_name ORDER BY quota_number ASC) AS invoice_names,
            COALESCE(SUM(age_30), 0) AS total_age_30,
            COALESCE(SUM(age_60), 0) AS total_age_60,
            COALESCE(SUM(age_90), 0) AS total_age_90,
            COALESCE(SUM(age_120), 0) AS total_age_120,
            COALESCE(SUM(age_older), 0) AS total_age_older,
            COALESCE(SUM(amount_residual), 0) AS total_due,
            COUNT(*) AS overdue_quota_count
        FROM saving_lines_data
        WHERE saving_id IS NOT NULL
        GROUP BY 
            saving_id, saving_name, partner_id, partner_name, partner_vat, state_plan
        HAVING 
            COALESCE(SUM(amount_residual), 0) > 0
        ORDER BY 
            partner_name, saving_name
        """
        
        # Agregar parámetros para los placeholders %s
        # company_id
        # params.append(company_id)
        
        try:
            # _logger.info("=== EJECUTANDO CONSULTA SQL ===")
            # _logger.info(f"Params count: {len(params)}")
            # _logger.info(f"Params: {params}")
            
            self.env.cr.execute(query)
            results = self.env.cr.dictfetchall()
            
            _logger.info(f"Resultados obtenidos: {len(results)} registros")
            
        except Exception as e:
            _logger.error(f"Error en consulta SQL: {str(e)}")
            _logger.error(f"Query: {query}")
            # Devolver estructura vacía en caso de error
            return {
                'report_date': report_date,
                'company_name': self.company_id.name,
                'data': [],
                'totals': {
                    'total_due': 0.0,
                    'total_age_30': 0.0,
                    'total_age_60': 0.0,
                    'total_age_90': 0.0,
                    'total_age_120': 0.0,
                    'total_age_older': 0.0,
                    'total_quota_count': 0,
                    'plan_count': 0,
                }
            }
        
        # Procesar resultados y construir estructura de datos
        report_data = []
        totals = {
            'total_due': 0.0,
            'total_age_30': 0.0,
            'total_age_60': 0.0,
            'total_age_90': 0.0,
            'total_age_120': 0.0,
            'total_age_older': 0.0,
            'total_quota_count': 0,
        }
        
        for row in results:
            # Construir líneas a partir de arrays
            lines = []
            if row.get('quota_numbers'):
                for i in range(len(row['quota_numbers'])):
                    residual = row['amount_residuals'][i] if row['amount_residuals'] and i < len(row['amount_residuals']) else 0.0
                    days_overdue = row['days_overdues'][i] if row['days_overdues'] and i < len(row['days_overdues']) else 0
                    
                    lines.append({
                        'line_id': row['line_ids'][i] if row['line_ids'] and i < len(row['line_ids']) else 0,
                        'quota_number': row['quota_numbers'][i],
                        'quota_date': row['quota_dates'][i],
                        'days_overdue': days_overdue,
                        'amount_total': row['amount_totals'][i] if row['amount_totals'] and i < len(row['amount_totals']) else 0.0,
                        'amount_paid': row['amount_paids'][i] if row['amount_paids'] and i < len(row['amount_paids']) else 0.0,
                        'amount_residual': residual,
                        'age_30': row['ages_30'][i] if row['ages_30'] and i < len(row['ages_30']) else 0.0,
                        'age_60': row['ages_60'][i] if row['ages_60'] and i < len(row['ages_60']) else 0.0,
                        'age_90': row['ages_90'][i] if row['ages_90'] and i < len(row['ages_90']) else 0.0,
                        'age_120': row['ages_120'][i] if row['ages_120'] and i < len(row['ages_120']) else 0.0,
                        'age_older': row['ages_older'][i] if row['ages_older'] and i < len(row['ages_older']) else 0.0,
                        'estado_pago': row['payment_states'][i] if row['payment_states'] and i < len(row['payment_states']) else '',
                        'invoice_name': row['invoice_names'][i] if row['invoice_names'] and i < len(row['invoice_names']) else '',
                    })
            
            # Obtener descripción del estado
            state_desc = ''
            for selection in self._fields['state_plan_filter'].selection:
                if selection[0] == row['state_plan']:
                    state_desc = selection[1]
                    break
            
            plan_data = {
                'saving_id': row['saving_id'],
                'saving_name': row['saving_name'],
                'partner_id': row['partner_id'],
                'partner_name': row['partner_name'],
                'partner_vat': row['partner_vat'] or '',
                'state_plan': row['state_plan'],
                'state_plan_description': state_desc,
                'lines': lines,
                'total_due': row['total_due'] or 0.0,
                'total_age_30': row['total_age_30'] or 0.0,
                'total_age_60': row['total_age_60'] or 0.0,
                'total_age_90': row['total_age_90'] or 0.0,
                'total_age_120': row['total_age_120'] or 0.0,
                'total_age_older': row['total_age_older'] or 0.0,
                'overdue_quota_count': row['overdue_quota_count'] or 0,
            }
            
            report_data.append(plan_data)
            
            # Acumular totales
            totals['total_due'] += row['total_due'] or 0.0
            totals['total_age_30'] += row['total_age_30'] or 0.0
            totals['total_age_60'] += row['total_age_60'] or 0.0
            totals['total_age_90'] += row['total_age_90'] or 0.0
            totals['total_age_120'] += row['total_age_120'] or 0.0
            totals['total_age_older'] += row['total_age_older'] or 0.0
            totals['total_quota_count'] += row['overdue_quota_count'] or 0
        
        totals['plan_count'] = len(report_data)
        
        return {
            'report_date': report_date,
            'company_name': self.company_id.name,
            'data': report_data,
            'totals': totals,
        }

    def get_report_data(self):
        """
        Método principal - usa la versión SQL optimizada
        """
        return self.get_report_data_sql()