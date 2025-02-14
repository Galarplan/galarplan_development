# -*- coding: utf-8 -*-
##############################################################################
#
#    ODOO, Open Source Management Solution
#    Copyright (C) 2016 Steigend IT Solutions
#    For more details, check COPYRIGHT and LICENSE files
#
##############################################################################
{
    'name': 'PDC management',
    'version': '16.0.1',
    'summary': """PDC Management""",
    'description': """Module manages PDC Based Payment Transaction""",
    'category': 'Account',
    'author': 'Steigend IT Solutions',
    'license': 'LGPL-3',
    'company': 'Steigend IT Solutions',
    'maintainer': 'Steigend IT Solutions',
    'website': "https://www.steigendit.com",
    'depends': ['payment','account_check_printing'],
    'data': [
        'data/pdc_data.xml',
        'data/data.xml',
        'security/ir.model.access.csv',
        'views/acc_pay_method_view.xml',
        'views/acc_payment_view.xml',
        'views/acc_payment_view_form_move.xml',
        'views/pdc_registr_view.xml',
        'views/menu.xml',
    ],
    'images': ['static/description/assets/images/cheque_img.png'],
    'currency': 'USD',
    'price': '20.0',
    'installable': True,
    'auto_install': False,
    'application': False,
}
