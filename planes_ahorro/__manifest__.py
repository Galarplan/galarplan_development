# -*- coding: utf-8 -*-
{
    'name': "planes_ahorro",

    'summary': """
        Módulo de planes de ahorro.    
    """,

    'description': """
        Módulo de planes de ahorro para la gestion de clientes los cuales
        depositan dinero en la empresa con el fin de que se le de un vehiculo.
    """,

    'author': "Luis Villacis",
    'website': "https://erp.forestdbs.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'l10n_ec'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/account_saving_plan.xml',
        'views/account_saving.xml',
        'views/ir_ui_menu.xml',

    ],
    'installable': True,
    'application': True,
    'assets': {
        'web.assets_backend': [
            'planes_ahorro/static/src/css/custom_style.css',
        ],
    },
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}
