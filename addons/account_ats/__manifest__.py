{
    'name': 'Cambios en Reportes Tributarios ATS,103,104,..etc',
    'version': '1.0',
    'category': 'Se agrega campos complementarios para reportes Tributarios',
    'description': """

    """,
    'author': "forestdbs",
    'website': 'www.forestdbs.com',
    'depends': ['base','account','report_xlsx_helper', 'l10n_ec_edi'],
    'data': [
        'security/ir.model.access.csv',
        'reports/ir_actions_report_xml.xml',
        'wizard/l10n_ec_ats.xml',
        'views/account_move.xml',
        'views/ir_ui_menu.xml',

    ],
    'installable': True,
}
