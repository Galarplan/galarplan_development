# -*- coding: utf-8 -*-
{
    'name': "check_print_format",

    'summary': """
        Formato de pagos con cheque para Galarplan 
    """,

    'description': """
        Formato de pagos con cheque para Galarplan
    """,

    'author': "Forestdbs",
    'website': "https://www.forestdbs.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'tools',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account_check_printing', 'account'],

    # always loaded
    'data': [
        'views/check_template.xml',  # Asegúrate de incluir el archivo XML aquí
        'reports/check_report.xml',
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}
