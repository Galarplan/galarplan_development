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
    'depends': ['base', 'l10n_ec','ventas_credito_cliente'],

    # always loaded
    'data': [
        'security/ir_module_category.xml',
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/ir_sequence.xml',
        'data/ir_cron.xml',
        'data/ir_config_parameter.xml',

        'reports/report_saving_state.xml',
        'reports/reports_menu.xml',

        "wizard/account_saving_payment_wizard.xml",
        'wizard/account_saving_wizard.xml',
        'wizard/account_saving_line_wizard.xml',
        'views/account_saving_plan.xml',
        'views/account_saving_lines.xml',
        'views/account_saving.xml',
        'views/account_saving_line_payment.xml',
        'views/account_move.xml',
        'views/res_company.xml',
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
