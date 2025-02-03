# -*- coding: utf-8 -*-
{
    'name': "credit_request",

    'summary': """
        credit request for customers/company    
    """,

    'description': """
        credit request for customers/company
    """,

    'author': "forestdbs",
    'website': "https://www.forestdbs.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'account',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','l10n_ec'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/customer_request.xml',
        'views/enterprise_request.xml',
        'views/menu_items.xml'
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}
