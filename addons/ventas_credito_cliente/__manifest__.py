{
    'name': 'Ventas a Crédito - Cuenta Contable en Cliente',
    'version': '16.0.1.0.0',
    'summary': 'Asigna automáticamente la cuenta por cobrar a crédito en facturas de clientes.',
    'author': 'TuNombre',
    'depends': ['account', 'sale'],
    'data': [
        'views/res_partner_views.xml',
        'views/account_move_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}