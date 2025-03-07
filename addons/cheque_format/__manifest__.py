{
    'name': 'Formato de impresion de cheques',
    'version': '1.0',
    'description': 'Formato para imprimir cheques',
    'summary': 'Formato para imprimir cheques',
    'author': 'Anthony Villacis',
    'website': '',
    'license': 'LGPL-3',
    'category': '',
    'depends': [
        'account',
        'base'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/cheque_format.xml',
        'views/account_payment.xml',
        'report/cheque_format.xml'
    ],
    'demo': [
        ''
    ],
    'auto_install': False,
    'application': False,
    'assets': {
        
    }
}