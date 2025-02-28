{
    'name': 'Migracion de facturas pagadas',
    'version': '1.0',
    'description': 'migracion de facturas pagadas',
    'summary': 'migracion de facturas pagadas',
    'author': 'anthony villacis',
    'website': 'www.ofrestdbs.com',
    'license': 'LGPL-3',
    'category': '',
    'depends': [
        'base',
        'account'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_move.xml'
    ],
    # 'demo': [
    #     ''
    # ],
    # 'auto_install': False,
    # 'application': False,
    # 'assets': {
        
    # }
}