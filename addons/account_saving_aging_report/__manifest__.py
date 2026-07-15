# -*- coding: utf-8 -*-
{
    'name': 'Reporte de Antigüedad de Cuotas por Cobrar - Planes de Ahorro',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'Reporte de vencimiento de cuotas de planes de ahorro',
    'description': """
        Módulo para generar reportes de antigüedad de cuotas por cobrar
        de planes de ahorro con opciones de exportación a Excel y PDF.
    """,
    'author': 'Tu Empresa',
    'website': 'https://www.tuempresa.com',
    'depends': [
        'base',
        'account',
        'planes_ahorro',
        'report_xlsx',  # Para exportación a Excel
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/saving_aging_wizard_views.xml',
        'views/menuviews.xml',
        'reports/saving_aging_report_template.xml',
        # 'data/report_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}