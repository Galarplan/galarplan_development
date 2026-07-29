# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import logging
import io
import base64
import xlsxwriter
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class SavingPortfolioWizard(models.TransientModel):
    _name = 'saving.portfolio.wizard'
    _description = 'Wizard para Reporte de Estructura de Cartera'

    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company
    )
    
    date_from = fields.Date(
        string='Fecha Inicial',
        required=True,
        default=fields.Date.today
    )
    
    date_to = fields.Date(
        string='Fecha Final',
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
    
    state_plan_ids = fields.Many2many(
        'account.saving.plan.type',
        string='Estados del Plan',
        help='Seleccionar uno o varios estados para filtrar'
    )
    
    show_zero_balance = fields.Boolean(
        string='Mostrar saldo cero',
        default=False,
        help='Mostrar planes con saldo pendiente igual a cero'
    )
    
    output_format = fields.Selection([
        ('pdf', 'PDF'),
        ('xlsx', 'Excel'),
    ], string='Formato de Salida', default='xlsx')

    def action_generate_report(self):
        """Genera el reporte según el formato seleccionado"""
        self.ensure_one()
        
        if self.output_format == 'xlsx':
            return self._export_xlsx()
        else:
            return self._export_pdf()
    
    def _export_pdf(self):
        """Exporta el reporte en formato PDF"""
        return self.env.ref('account_saving_aging_report.action_report_saving_portfolio').report_action(self)
    
    def _get_portfolio_data(self):
        """Obtiene los datos del reporte de cartera usando CTE optimizado"""
        date_from = self.date_from
        date_to = self.date_to
        company_id = self.company_id.id
        
        # Construir filtros
        partner_filter = ""
        saving_filter = ""
        state_filter = ""
        date_filter = f"WHERE rs.start_date BETWEEN '{date_from}'::date and '{date_to}'::date"
        
        if self.partner_ids and self.partner_ids.ids:
            ids = tuple(self.partner_ids.ids)
            partner_filter = f"AND as1.partner_id IN {ids}" if len(ids) > 1 else f"AND as1.partner_id = {ids[0]}"
            date_filter = ""
        if self.saving_plan_ids and self.saving_plan_ids.ids:
            ids = tuple(self.saving_plan_ids.ids)
            saving_filter = f"AND as1.id IN {ids}" if len(ids) > 1 else f"AND as1.id = {ids[0]}"
        
        if self.state_plan_ids and self.state_plan_ids.ids:
            codes = [f"'{state.code}'" for state in self.state_plan_ids]
            state_filter = f"AND as1.state_plan IN ({','.join(codes)})"
        
        


        query = f"""
        WITH fecha_corte AS (
            SELECT '{date_from}'::date AS fecha_inicio,
                   '{date_to}'::date AS fecha_fin
        ),
        lineas_cuotas AS (
            SELECT 
                asl.saving_id,
                asl.principal_amount,
                asl.serv_admin_amount,
                asl.seguro_amount,
                asl.saving_amount,
                asl.pendiente,
                asl.date,
                asl.estado_pago,
                (asl.principal_amount + asl.serv_admin_amount + asl.seguro_amount) AS total_cuota,
                (SELECT fecha_fin FROM fecha_corte) - asl.date AS days_diff
            FROM account_saving_lines asl
            WHERE asl.estado_pago IN ('pendiente', 'sin_aplicar', 'pagado')
        ),
        resumen_plan AS (
            SELECT 
                as1.id,
                as1.name,
                as1.start_date,
                as1.end_date,
                as1.state_plan,
                as1.saving_amount,
                as1.quota_amount,
                COALESCE(MAX(
                	CASE 
                    WHEN lc.estado_pago IN ('pendiente', 'sin_aplicar') 
                        AND lc.pendiente > 0 
                        AND lc.date < (SELECT fecha_fin FROM fecha_corte) 
                    THEN lc.saving_amount
                END
                ),0) as cuota,
                as1.pendiente,
                as1.partner_id,
                as1.seller_id,
                -- Saldos
                COALESCE(SUM(CASE WHEN lc.estado_pago IN ('pendiente', 'sin_aplicar') THEN lc.principal_amount ELSE 0 END), 0) AS saldo_capital,
                COALESCE(SUM(CASE WHEN lc.estado_pago IN ('pendiente', 'sin_aplicar') THEN lc.pendiente ELSE 0 END), 0) AS saldo_total,
                -- Cuotas vencidas
                COUNT(CASE 
                    WHEN lc.estado_pago IN ('pendiente', 'sin_aplicar') 
                        AND lc.pendiente > 0 
                        AND lc.date < (SELECT fecha_fin FROM fecha_corte) 
                    THEN 1 
                END) AS cuotas_vencidas,
                -- Días de mora
                --COALESCE(
                --    EXTRACT(DAY FROM (age((SELECT fecha_fin FROM fecha_corte), MIN(CASE 
                --        WHEN lc.estado_pago IN ('pendiente', 'sin_aplicar') 
                --            AND lc.pendiente > 0 
                --            AND lc.date < (SELECT fecha_fin FROM fecha_corte) 
                --        THEN lc.date 
                --    END)))),
                --    0
                --) AS dias_mora,
                COALESCE(
				    (SELECT fecha_fin FROM fecha_corte) - MIN(CASE 
				        WHEN lc.estado_pago IN ('pendiente', 'sin_aplicar') 
				            AND lc.pendiente > 0 
				            AND lc.date < (SELECT fecha_fin FROM fecha_corte) 
				        THEN lc.date 
				    END),
				    0
				) AS dias_mora,
                -- MADURACIÓN DE CAPITAL (principal_amount)
                COALESCE(SUM(CASE 
                    WHEN lc.estado_pago IN ('pendiente', 'sin_aplicar') 
                        AND lc.days_diff BETWEEN 0 AND 30 
                    THEN lc.principal_amount ELSE 0 END), 0) AS capital_30_dias,
                COALESCE(SUM(CASE 
                    WHEN lc.estado_pago IN ('pendiente', 'sin_aplicar') 
                        AND lc.days_diff BETWEEN 31 AND 90 
                    THEN lc.principal_amount ELSE 0 END), 0) AS capital_90_dias,
                COALESCE(SUM(CASE 
                    WHEN lc.estado_pago IN ('pendiente', 'sin_aplicar') 
                        AND lc.days_diff BETWEEN 91 AND 180 
                    THEN lc.principal_amount ELSE 0 END), 0) AS capital_180_dias,
                COALESCE(SUM(CASE 
                    WHEN lc.estado_pago IN ('pendiente', 'sin_aplicar') 
                        AND lc.days_diff BETWEEN 181 AND 270 
                    THEN lc.principal_amount ELSE 0 END), 0) AS capital_270_dias,
                COALESCE(SUM(CASE 
                    WHEN lc.estado_pago IN ('pendiente', 'sin_aplicar') 
                        AND lc.days_diff BETWEEN 271 AND 360 
                    THEN lc.principal_amount ELSE 0 END), 0) AS capital_360_dias,
                COALESCE(SUM(CASE 
                    WHEN lc.estado_pago IN ('pendiente', 'sin_aplicar') 
                        AND lc.days_diff > 360 
                    THEN lc.principal_amount ELSE 0 END), 0) AS capital_mas_360_dias,
                -- Capital por vencer (futuro)
                COALESCE(SUM(CASE 
                    WHEN lc.estado_pago IN ('pendiente', 'sin_aplicar') 
                        AND lc.date > (SELECT fecha_fin FROM fecha_corte) 
                    THEN lc.principal_amount ELSE 0 END), 0) AS capital_por_vencer,
                -- MADURACIÓN TOTAL CUOTA
                COALESCE(SUM(CASE 
                    WHEN lc.estado_pago IN ('pendiente', 'sin_aplicar') 
                        AND lc.days_diff BETWEEN 0 AND 30 
                    THEN lc.total_cuota ELSE 0 END), 0) AS cuota_30_dias,
                COALESCE(SUM(CASE 
                    WHEN lc.estado_pago IN ('pendiente', 'sin_aplicar') 
                        AND lc.days_diff BETWEEN 31 AND 90 
                    THEN lc.total_cuota ELSE 0 END), 0) AS cuota_90_dias,
                COALESCE(SUM(CASE 
                    WHEN lc.estado_pago IN ('pendiente', 'sin_aplicar') 
                        AND lc.days_diff BETWEEN 91 AND 180 
                    THEN lc.total_cuota ELSE 0 END), 0) AS cuota_180_dias,
                COALESCE(SUM(CASE 
                    WHEN lc.estado_pago IN ('pendiente', 'sin_aplicar') 
                        AND lc.days_diff BETWEEN 181 AND 270 
                    THEN lc.total_cuota ELSE 0 END), 0) AS cuota_270_dias,
                COALESCE(SUM(CASE 
                    WHEN lc.estado_pago IN ('pendiente', 'sin_aplicar') 
                        AND lc.days_diff BETWEEN 271 AND 360 
                    THEN lc.total_cuota ELSE 0 END), 0) AS cuota_360_dias,
                COALESCE(SUM(CASE 
                    WHEN lc.estado_pago IN ('pendiente', 'sin_aplicar') 
                        AND lc.days_diff > 360 
                    THEN lc.total_cuota ELSE 0 END), 0) AS cuota_mas_360_dias,
                -- Cuota por vencer (futuro)
                COALESCE(SUM(CASE 
                    WHEN lc.estado_pago IN ('pendiente', 'sin_aplicar') 
                        AND lc.date > (SELECT fecha_fin FROM fecha_corte) 
                    THEN lc.total_cuota ELSE 0 END), 0) AS cuota_por_vencer,
                -- Gastos pagados
                --COALESCE(SUM(CASE WHEN lc.estado_pago = 'pagado' THEN lc.serv_admin_amount ELSE 0 END), 0) AS gastos_legales,
                am2.amount_total AS gastos_legales,
                COALESCE(SUM(CASE WHEN lc.estado_pago = 'pagado' THEN lc.seguro_amount ELSE 0 END), 0) AS valor_seguro,
                --COALESCE(SUM(CASE WHEN lc.estado_pago = 'pagado' THEN lc.serv_admin_amount ELSE 0 END), 0) AS valor_dispositivo,
                am3.amount_total AS valor_dispositivo,
                -- Gastos de cobranza (1% por cada 30 días de mora)
                COALESCE(SUM(CASE 
				    WHEN lc.estado_pago IN ('pendiente', 'sin_aplicar') 
				        AND lc.pendiente > 0 
				        AND lc.date < (SELECT fecha_fin FROM fecha_corte)
				    THEN 
				        CASE 
				            WHEN lc.total_cuota <= 19.99 THEN 3
				            WHEN lc.total_cuota BETWEEN 20 AND 39.99 THEN 5
				            WHEN lc.total_cuota BETWEEN 40 AND 59.99 THEN 9
				            WHEN lc.total_cuota BETWEEN 60 AND 79.99 THEN 12
				            WHEN lc.total_cuota BETWEEN 80 AND 100 THEN 15
				            WHEN lc.total_cuota > 100 THEN 18
				            ELSE 0
				        END
				    ELSE 0 END), 0) AS gastos_cobranza
            FROM account_saving as1
            LEFT JOIN lineas_cuotas lc ON lc.saving_id = as1.id
            LEFT JOIN account_move am1 on am1.id = as1.vehicle_invoice_id
            LEFT JOIN account_move am2 on am2.id = as1.legal_invoice_id
            LEFT JOIN account_move am3 on am3.id = as1.device_invoice_id
            WHERE as1.company_id = {company_id}
                {partner_filter}
                {saving_filter}
                {state_filter}
            GROUP BY 
                as1.id, as1.name, as1.start_date, as1.end_date, as1.state_plan,
                as1.saving_amount, as1.quota_amount, as1.pendiente, as1.partner_id, as1.seller_id,am2.amount_total,am3.amount_total
        )
        SELECT 
            rp.vat AS identificacion, 
            rp.name AS cliente,
            rs.name AS nombre_plan,
            SPLIT_PART(rs.name, '-', 1) AS grupo_plan_ahorro,
            SPLIT_PART(rs.name, '-', 2) AS codigo_del_plan,
            rs.state_plan AS estado,
            rs.dias_mora,
            rs.start_date AS inicio,
            rs.end_date AS vencimiento,
            rs.saving_amount AS valor_del_plan,
            rs.saldo_capital,
            rs.saldo_total,
            --rs.quota_amount AS valor_de_cuota,
            rs.cuota as valor_de_cuota,
            rs.cuotas_vencidas,
            -- Maduración de capital
            rs.capital_30_dias,
            rs.capital_90_dias,
            rs.capital_180_dias,
            rs.capital_270_dias,
            rs.capital_360_dias,
            rs.capital_mas_360_dias,
            rs.capital_por_vencer,
            -- Maduración total cuota
            rs.cuota_30_dias,
            rs.cuota_90_dias,
            rs.cuota_180_dias,
            rs.cuota_270_dias,
            rs.cuota_360_dias,
            rs.cuota_mas_360_dias,
            rs.cuota_por_vencer,
            -- Gastos
            rs.gastos_legales,
            rs.valor_seguro,
            rs.valor_dispositivo,
            rs.gastos_cobranza,
            --ru.name AS official_cartera,
            -- Tasa de interés (para reestructurados)
            CASE WHEN rs.state_plan = 'estructured' THEN 12.0 ELSE 0.0 END AS tasa_interes,
            -- Interés de mora cancelado
            0 AS interes_mora_cancelado,
            -- Valor castigo (futuro)
            0 AS valor_castigo,
            -- Provisión requerida (20% del saldo pendiente si mora > 60 días)
            CASE 
                WHEN rs.dias_mora >= 60 THEN rs.saldo_total * 0.20
                ELSE 0
            END AS provision_requerida
        FROM resumen_plan rs
        INNER JOIN res_partner rp ON rp.id = rs.partner_id
        LEFT JOIN res_users ru ON ru.id = rs.seller_id
        {date_filter}
        ORDER BY rp.name, rs.name
        """
        
        try:
            print('==================================',query)
            self.env.cr.execute(query)
            results = self.env.cr.dictfetchall()
            _logger.info(f"Portfolio report results: {len(results)} registros")
        except Exception as e:
            _logger.error(f"Error en consulta de cartera: {str(e)}")
            _logger.error(f"Query: {query}")
            return []
        
        return results
    
    def _export_xlsx(self):
        """Exporta el reporte en formato Excel con la estructura de cartera"""
        data = self._get_portfolio_data()
        
        if not data:
            raise ValidationError(_('No hay datos para exportar con los filtros seleccionados.'))
        
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
            'text_wrap': True,
        })
        
        header_green = workbook.add_format({
            'bold': True,
            'bg_color': '#27ae60',
            'color': 'white',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'font_size': 10,
            'text_wrap': True,
        })
        
        header_blue = workbook.add_format({
            'bold': True,
            'bg_color': '#2980b9',
            'color': 'white',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'font_size': 10,
            'text_wrap': True,
        })
        
        money_format = workbook.add_format({
            'num_format': '#,##0.00',
            'align': 'right',
            'valign': 'vcenter',
            'border': 1,
            'font_size': 9,
        })
        
        money_red_format = workbook.add_format({
            'num_format': '#,##0.00',
            'align': 'right',
            'valign': 'vcenter',
            'border': 1,
            'font_size': 9,
            'color': '#c0392b',
        })
        
        money_green_format = workbook.add_format({
            'num_format': '#,##0.00',
            'align': 'right',
            'valign': 'vcenter',
            'border': 1,
            'font_size': 9,
            'color': '#27ae60',
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
        
        # Crear hoja principal
        sheet = workbook.add_worksheet('Estructura Cartera')
        
        # Definir anchos de columnas
        column_widths = {
            'A': 15,   # Identificación
            'B': 35,   # Cliente
            'C': 15,   # Grupo Plan
            'D': 20,   # Código del plan
            'E': 20,   # Nombre del plan
            'F': 12,   # Estado
            'G': 12,   # Días mora
            'H': 12,   # Fecha emisión
            'I': 14,   # Fecha vencimiento
            'J': 14,   # Valor del plan
            'K': 14,   # Saldo capital
            'L': 14,   # Saldo total
            'M': 10,   # Valor de cuota
            'N': 14,   # Cuotas vencidas
            'O': 14,   # capital 30 dias
            'P': 14,   # capital 90 dias
            'Q': 14,   # capital 120 dias
            'R': 14,   # capital 270 dias
            'S': 14,   # capital 360 dias
            'T': 14,   # capital mas de 360
            'U': 14,   # saldo por vencer
            'V': 14,   # cuota 30 dias
            'W': 14,   # cuota 90 dias
            'X': 25,   # cuota 120 dias
            'Y': 20,   # cuota 270 dias
            'Z': 20,   # cuota 360 dias
            'AA': 20,  # cuota mas de 360
            'AB': 20,  # cuota por vencer
            'AC': 20,  # Gastos legales cancelados
            'AD': 20,  # valor dispositivo cancelado
            'AE': 20,  # valor seguro vehicular cancelad
            'AF': 20,  # gastos de cobranza 
            'AG': 20,  # tasa de interes
            'AH': 20,  # interes de mora
            'AI': 20,  # valor castigo
            'AJ': 20,  # prov requerida
            'AK': 20,  # Tipo de garantia
        }
        
        for col, width in column_widths.items():
            sheet.set_column(f'{col}:{col}', width)
        
        row = 0
        
        # Título del reporte
        sheet.merge_range(row, 0, row, 24, 'ESTRUCTURA DE CARTERA – CUENTAS POR COBRAR', header_format)
        row += 1
        
        # Información del reporte
        sheet.merge_range(row, 0, row, 5, f'Fecha de Corte: {self.date_to.strftime("%d/%m/%Y")}', text_format)
        sheet.merge_range(row, 6, row, 10, f'Período: {self.date_from.strftime("%d/%m/%Y")} - {self.date_to.strftime("%d/%m/%Y")}', text_format)
        sheet.write(row, 11, f'Total Registros: {len(data)}', text_format)
        row += 2
        
        # Cabeceras principales
        headers = [
            '# Identificación', 'Cliente', '# Grupo Plan', 'Código del plan', 'Estado',
            'Días mora', 'Fecha emisión', 'Fecha vencimiento', 'Valor del plan',
            'Saldo capital', 'Saldo total', 'Valor de cuota', '# Cuotas vencidas',
            '30 dias', '90 dias', '180 dias', '270 dias', '360 dias', '+ 360 dias','Capital por vencer','30 dias', '90 dias', '180 dias', '270 dias', '360 dias', '+ 360 dias','Cuota por vencer', 'Gastos Legales',
            'Valor Dispositivo', 'Valor Seguro', 'Gastos de Cobranzas',
            'Tasa de interés', 'Interés de mora cancelado', 'Valor castigo',
            'Provisión requerida', 'Tipo de Garantía', 'Oficial de cartera'
        ]

        COLUMNS = {
            'identificacion': 0,
            'cliente': 1,
            'grupo_plan': 2,
            'codigo_plan': 3,
            'estado': 4,
            'dias_mora': 5,
            'fecha_emision': 6,
            'fecha_vencimiento': 7,
            'valor_plan': 8,
            'saldo_capital': 9,
            'saldo_total': 10,
            'valor_cuota': 11,
            'cuotas_vencidas': 12,
            'capital_30': 13,
            'capital_90': 14,
            'capital_180': 15,
            'capital_270': 16,
            'capital_360': 17,
            'capital_mas_360': 18,
            'capital_por_vencer': 19,
            'cuota_30': 20,
            'cuota_90': 21,
            'cuota_180': 22,
            'cuota_270': 23,
            'cuota_360': 24,
            'cuota_mas_360': 25,
            'cuota_por_vencer': 26,
            'gastos_legales': 27,
            'valor_dispositivo': 28,
            'valor_seguro': 29,
            'gastos_cobranza': 30,
            'tasa_interes': 31,
            'interes_mora': 32,
            'valor_castigo': 33,
            'provision': 34,
            'tipo_garantia': 35,
            'oficial': 36,
        }

        
        # Colores alternados para cabeceras
        for col, header in enumerate(headers):
            if col in [0, 1, 2, 3, 4, 5, 6, 7]:  # Información del cliente
                fmt = header_format
            elif col in [8, 9, 10, 11, 12]:  # Valores del plan
                fmt = header_green
            elif col in [13, 14,15,16,17,18,19,20,21,22,23,24,25,26]:  # Maduración
                fmt = header_blue
            else:
                fmt = header_format
            sheet.write(row, col, header, fmt)
        row += 1
        
        # Datos
        totals = {
            'saving_amount': 0,
            'capital_balance': 0,
            'total_balance': 0,
            'legal_expenses': 0,
            'device_value': 0,
            'insurance_value': 0,
            'required_provision': 0,
            'overdue_quotas': 0,
            'gastos_cobranza': 0,  # Nuevo
            'capital_30': 0,       # Nuevo
            'capital_90': 0,       # Nuevo
            'capital_180': 0,      # Nuevo
            'capital_270': 0,      # Nuevo
            'capital_360': 0,      # Nuevo
            'capital_mas_360': 0,  # Nuevo
            'capital_por_vencer': 0, # Nuevo
            'cuota_30': 0,         # Nuevo
            'cuota_90': 0,         # Nuevo
            'cuota_180': 0,        # Nuevo
            'cuota_270': 0,        # Nuevo
            'cuota_360': 0,        # Nuevo
            'cuota_mas_360': 0,    # Nuevo
            'cuota_por_vencer': 0, # Nuevo
        }
        
        for record in data:
            # Obtener el grupo del plan (primeros dígitos del nombre)
            saving_name = record.get('nombre_plan', '')
            group_plan = saving_name.split('-')[0] if '-' in saving_name else saving_name[:3]
            
            # Mapeo de estados
            state_map = {
                'draft': 'Borrador',
                'posted': 'Publicado',
                'active': 'Activo',
                'adjudicated_with_assets': 'Adjudicado con Bien',
                'adjudicated_without_assets': 'Adjudicado sin Bien',
                'awarded': 'Adjudicado',
                'pending_authorizated': 'Autorización de Retiro Pendiente',
                'anulled': 'Anulado',
                'disabled': 'Desactivado',
                'retired': 'Retirado',
                'precanceled': 'Pre-Cancelado',
                'estructured': 'Re-estructurado',
                'cancelled': 'Cancelado',
                'moved': 'Traspaso',
                'closed': 'Cerrado',
            }
            state_desc = state_map.get(record.get('estado', ''), record.get('estado', ''))
            
            # Escribir datos
            sheet.write(row, 0, record.get('identificacion', ''), text_format)
            sheet.write(row, 1, record.get('cliente', ''), text_format)
            sheet.write(row, 2, record.get('grupo_plan_ahorro', ''), text_center_format)
            sheet.write(row, 3, record.get('codigo_del_plan', ''), text_format)
            sheet.write(row, 4, state_desc, text_format)
            sheet.write(row, 5, max(0, record.get('dias_mora', 0) or 0), text_center_format)
            sheet.write(row, 6, record.get('inicio').strftime('%d/%m/%Y') if record.get('inicio') else '', text_center_format)
            sheet.write(row, 7, record.get('vencimiento').strftime('%d/%m/%Y') if record.get('vencimiento') else '', text_center_format)
            
            # Valores monetarios
            sheet.write(row, 8, record.get('valor_del_plan', 0), money_format)
            sheet.write(row, 9, record.get('saldo_capital', 0), money_format)
            sheet.write(row, 10, record.get('saldo_total', 0), money_red_format)
            sheet.write(row, 11, record.get('valor_de_cuota', 0), money_format)
            sheet.write(row, 12, record.get('cuotas_vencidas', 0), text_center_format)
            
            # Maduración de capital
            sheet.write(row, 13, record.get('capital_30_dias', 0) ,money_format)
            sheet.write(row, 14, record.get('capital_90_dias', 0), money_format)
            sheet.write(row, 15, record.get('capital_180_dias', 0) , money_format)
            sheet.write(row, 16, record.get('capital_270_dias', 0) , money_format)
            sheet.write(row, 17, record.get('capital_360_dias', 0) , money_format)
            sheet.write(row, 18, record.get('capital_mas_360_dias', 0), money_format)
            sheet.write(row, 19, record.get('capital_por_vencer', 0), money_format)
        
            # Maduración total cuota
            sheet.write(row, 20, record.get('cuota_30_dias', 0), money_format)
            sheet.write(row, 21, record.get('cuota_90_dias', 0), money_format)
            sheet.write(row, 22, record.get('cuota_180_dias', 0), money_format)
            sheet.write(row, 23, record.get('cuota_270_dias', 0), money_format)
            sheet.write(row, 24, record.get('cuota_360_dias', 0), money_format)
            sheet.write(row, 25, record.get('cuota_mas_360_dias', 0), money_format)
            sheet.write(row, 26, record.get('cuota_por_vencer', 0), money_format)
            

            # Gastos
            sheet.write(row, 27, record.get('gastos_legales', 0), money_format)
            sheet.write(row, 28, record.get('valor_dispositivo', 0), money_format)
            sheet.write(row, 29, record.get('valor_seguro', 0), money_format)
            sheet.write(row, 30, record.get('gastos_cobranza', 0), money_format)
            sheet.write(row, 31, record.get('tasa_interes', 0), money_format)
            sheet.write(row, 32, record.get('interes_mora_cancelado', 0), money_format)
            sheet.write(row, 33, record.get('valor_castigo', 0), money_format)
            
            # Provisión
            provision = record.get('provision_requerida', 0)
            sheet.write(row, 34, provision, money_red_format if provision > 0 else money_format)
            
            sheet.write(row, 35, record.get('vehicle_info', ''), text_format)
            sheet.write(row, 36, record.get('official_cartera', ''), text_format)
            
            # Acumular totales
            totals['saving_amount'] += record.get('valor_del_plan', 0) or 0
            totals['capital_balance'] += record.get('saldo_capital', 0) or 0
            totals['total_balance'] += record.get('saldo_total', 0) or 0
            totals['legal_expenses'] += record.get('gastos_legales', 0) or 0
            totals['device_value'] += record.get('valor_dispositivo', 0) or 0
            totals['insurance_value'] += record.get('valor_seguro', 0) or 0
            totals['required_provision'] += record.get('provision_requerida', 0) or 0
            totals['overdue_quotas'] += record.get('cuotas_vencidas', 0) or 0
            totals['gastos_cobranza'] += record.get('gastos_cobranza', 0) or 0
            
            # Totales de maduración de capital
            totals['capital_30'] += record.get('capital_30_dias', 0)
            totals['capital_90'] += record.get('capital_90_dias', 0)
            totals['capital_180'] += record.get('capital_180_dias', 0)
            totals['capital_270'] += record.get('capital_270_dias', 0)
            totals['capital_360'] += record.get('capital_360_dias', 0)
            totals['capital_mas_360'] += record.get('capital_mas_360_dias', 0)
            totals['capital_por_vencer'] += record.get('capital_por_vencer', 0)
            
            # Totales de maduración de cuota
            totals['cuota_30'] += record.get('cuota_30_dias', 0)
            totals['cuota_90'] += record.get('cuota_90_dias', 0)
            totals['cuota_180'] += record.get('cuota_180_dias', 0)
            totals['cuota_270'] += record.get('cuota_270_dias', 0)
            totals['cuota_360'] += record.get('cuota_360_dias', 0)
            totals['cuota_mas_360'] += record.get('cuota_mas_360_dias', 0)
            totals['cuota_por_vencer'] += record.get('cuota_por_vencer', 0)
            
            row += 1
        
        # Totales finales
        row += 1
        sheet.write(row, COLUMNS['codigo_plan'], 'TOTALES', total_format)
        sheet.write(row, COLUMNS['valor_plan'], totals['saving_amount'], total_format)
        sheet.write(row, COLUMNS['saldo_capital'], totals['capital_balance'], total_format)
        sheet.write(row, COLUMNS['saldo_total'], totals['total_balance'], total_format)
        sheet.write(row, COLUMNS['valor_cuota']+1, totals['overdue_quotas'], total_format)

        # Totales de maduración de capital
        sheet.write(row, COLUMNS['capital_30'], totals['capital_30'], total_format)
        sheet.write(row, COLUMNS['capital_90'], totals['capital_90'], total_format)
        sheet.write(row, COLUMNS['capital_180'], totals['capital_180'], total_format)
        sheet.write(row, COLUMNS['capital_270'], totals['capital_270'], total_format)
        sheet.write(row, COLUMNS['capital_360'], totals['capital_360'], total_format)
        sheet.write(row, COLUMNS['capital_mas_360'], totals['capital_mas_360'], total_format)
        sheet.write(row, COLUMNS['capital_por_vencer'], totals['capital_por_vencer'], total_format)

        # Totales de maduración de cuota
        sheet.write(row, COLUMNS['cuota_30'], totals['cuota_30'], total_format)
        sheet.write(row, COLUMNS['cuota_90'], totals['cuota_90'], total_format)
        sheet.write(row, COLUMNS['cuota_180'], totals['cuota_180'], total_format)
        sheet.write(row, COLUMNS['cuota_270'], totals['cuota_270'], total_format)
        sheet.write(row, COLUMNS['cuota_360'], totals['cuota_360'], total_format)
        sheet.write(row, COLUMNS['cuota_mas_360'], totals['cuota_mas_360'], total_format)
        sheet.write(row, COLUMNS['cuota_por_vencer'], totals['cuota_por_vencer'], total_format)

        # Totales de gastos
        sheet.write(row, COLUMNS['gastos_legales'], totals['legal_expenses'], total_format)
        sheet.write(row, COLUMNS['valor_dispositivo'], totals['device_value'], total_format)
        sheet.write(row, COLUMNS['valor_seguro'], totals['insurance_value'], total_format)
        sheet.write(row, COLUMNS['gastos_cobranza'], totals['gastos_cobranza'], total_format)
        sheet.write(row, COLUMNS['provision'], totals['required_provision'], total_format)
        
        workbook.close()
        output.seek(0)
        
        # Guardar el archivo
        xlsx_data = base64.b64encode(output.getvalue())
        filename = f"Estructura_Cartera_{fields.Date.today().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': xlsx_data,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'res_model': self._name,
            'res_id': self.id,
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }