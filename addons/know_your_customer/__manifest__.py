# -*- coding: utf-8 -*-
{
    'name': "know_your_client",

    'summary': """
        Formulario de conozca a su cliente""",

    'description': """
        Formulario de conozca a su cliente
    """,

    'author': "Forestdbs",
    'website': "https://www.forestdbs.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','credit_request'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/know_your_client.xml',
        'views/menuitems.xml',
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}
