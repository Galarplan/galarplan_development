{
    'name': 'Reporte de Recaudación Diaria',
    'version': '1.0',
    'author': 'Tu Nombre',
    'category': 'Accounting',
    'summary': 'Genera reportes de recaudación diaria',
    'depends': ['base', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/daily_collection_wizard.xml',
        'reports/daily_collection_report.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
