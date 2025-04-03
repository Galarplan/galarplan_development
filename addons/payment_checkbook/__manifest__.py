{
    'name': 'Talonario de cheques',
    'version': '1.0',
    'description': 'Talonario de cheques',
    'summary': 'Talonario de cheques',
    'author': 'Anthony Villacis',
    'website': 'www.forestdbs.com',
    'license': 'LGPL-3',
    'category': '',
    'depends': [
        'base',
        'account'
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/payment_checkbook.xml',
        'views/account_payment.xml',
    ],
    # 'demo': [
    #     ''
    # ],
    # 'auto_install': False,
    # 'application': False,
    # 'assets': {
        
    # }
}