# -*- coding: utf-8 -*-
{
    'name': 'plan 50+1',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'Gestión de 50+1',
    'description': """
        Módulo para la gestión de Planes de Ahorro
    """,
    'author': 'Tu Empresa',
    'website': 'https://www.tuempresa.com',
    'depends': [
        'planes_ahorro',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'wizard/payment_inscription.xml',
        'views/account_saving.xml',
        # 'views/planes_ahorro.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}