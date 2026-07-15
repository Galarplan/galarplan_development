# -*- coding: utf-8 -*-

from odoo import models, api, fields, _
from odoo.exceptions import UserError
import logging
from decimal import Decimal

_logger = logging.getLogger(__name__)


class SavingAgingReportPDF(models.AbstractModel):
    _name = 'report.account_saving_aging_report.saving_aging_report_pdf'
    _description = 'Reporte PDF de Antigüedad de Cuotas de Ahorro'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        if not docids:
            raise UserError(_('No se encontraron registros para generar el reporte.'))
        
        wizard = self.env['saving.aging.wizard'].browse(docids[0])
        
        if not wizard.exists():
            raise UserError(_('El wizard no existe o ha sido eliminado.'))
        
        # Obtener datos del reporte
        report_data = wizard.get_report_data()
        
        # Verificar si hay datos
        if not report_data.get('data'):
            return {
                'doc_ids': docids,
                'doc_model': 'saving.aging.wizard',
                'docs': wizard,
                'data': report_data,
                'has_data': False,
                'no_data_message': 'No se encontraron datos para los filtros seleccionados.',
            }
        
        # Calcular subtotales por socio
        partner_summary = {}
        for item in report_data['data']:
            partner_id = item['partner_id']
            if partner_id not in partner_summary:
                partner_summary[partner_id] = {
                    'partner_name': item['partner_name'],
                    'partner_vat': item['partner_vat'],
                    'plans': [],
                    'total_residual': 0.0,
                    'total_not_due': 0.0,
                    'total_30': 0.0,
                    'total_60': 0.0,
                    'total_90': 0.0,
                    'total_120': 0.0,
                    'total_older': 0.0,
                }
            partner_summary[partner_id]['plans'].append(item)
            partner_summary[partner_id]['total_residual'] += item['total_residual']
            partner_summary[partner_id]['total_not_due'] += item['total_not_due']
            partner_summary[partner_id]['total_30'] += item['total_30']
            partner_summary[partner_id]['total_60'] += item['total_60']
            partner_summary[partner_id]['total_90'] += item['total_90']
            partner_summary[partner_id]['total_120'] += item['total_120']
            partner_summary[partner_id]['total_older'] += item['total_older']
        
        # Fecha de generación
        today = fields.Date.today()
        currency = wizard.company_id.currency_id
        
        # Función para formatear moneda
        def format_currency(amount):
            if amount is None:
                return "0.00"
            if isinstance(amount, Decimal):
                amount = float(amount)
            if abs(amount) < 0.005:
                return "0.00"
            try:
                if currency:
                    return currency.format(amount)
                return f"{amount:,.2f}"
            except:
                return f"{amount:,.2f}"
        
        print('==================',report_data)

        return {
            'doc_ids': docids,
            'doc_model': 'saving.aging.wizard',
            'docs': wizard,
            'data': report_data,
            'partner_summary': partner_summary,
            'generation_date': today,
            'format_currency': format_currency,
            'has_data': True,
        }