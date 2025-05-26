{
    'name': 'Recibos de cobro',
    'version': '1.0',
    'description': 'Recibos y comprobacion de cobros',
    'summary': 'Recibos y comprobacion de cobros',
    'author': 'Anthony Villacis',
    'website': 'www.forestdbs.com',
    'license': 'LGPL-3',
    'category': '',
    'depends': [
        'base',
        'account',
        'planes_ahorro'
    ],
    'data': [
        'security/groups.xml',
        'security/validator_groups.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'view_sql/receipt_plan.xml',
        'report/receipt_paperformat.xml',
        'report/receipt_template.xml',
        'report/validation_rceipt_template.xml',
        'report/receipt_report.xml',
        'views/receipt_validation_views.xml',
        'views/menus.xml',
    ],
    # 'demo': [
    #     ''
    # ],
    # 'auto_install': False,
    # 'application': False,
    # 'assets': {
        
    # }
}