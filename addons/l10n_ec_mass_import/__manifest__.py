{
    'name': 'Carga Masiva contable',
    'version': '16.0.1.0',
    'summary': 'Importacion masiva de facturas,retenciones,pagos',
    'author': 'Antthnoy villacis',
    'depends': ['account'],
    'data': [
        "security/ir.model.access.csv",
        'wizard/l10n_ec_import_witholds.xml',
    ],
    'installable': True,
    'application': False,
}