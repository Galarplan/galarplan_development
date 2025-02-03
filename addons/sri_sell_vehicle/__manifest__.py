# -*- coding: utf-8 -*-
{
    'name': "Registro de vehiculos SRI",

    'summary': """Modulo de registro de vehiculos en el SRI""",

    'description': """
        Modulo de registro de vehiculos en el SRI
    """,

    'author': "Forestdbs",
    'website': "https://www.forestdbs.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','stock'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'views/views.xml',
        'views/res_country_state.xml',
        'views/res_country_substate.xml',
        'views/res_partner.xml',
        'wizzard/invoice_sri.xml',
        'views/menuitems.xml',
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}
