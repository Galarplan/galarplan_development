{
    'name': 'Cargar cuentas contables',
    'version': '1.0',
    'description': 'cargar cuentas contables',
    'summary': 'cargar cuentas contables',
    'author': 'anthony villacis',
    'website': '',
    'license': 'LGPL-3',
    'category': '',
    'depends': [
        'base','account'
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/load_accounts.xml',
        # 'wizard/load_budget_relationship.xml'
    ],
}