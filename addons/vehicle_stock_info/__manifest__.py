# -*- coding: utf-8 -*-
{
    'name': "vehicle_stock_info",

    'summary': """
        agregar informacion en stock para vehiculo""",

    'description': """
        agregar informacion en stock para vehiculo
    """,

    'author': "forestdbs",
    'website': "https://www.forestdbs.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Stock',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','stock','account','l10n_ec_edi'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'views/views.xml',
        # 'views/templates.xml',
        'views/vehicle_stock_info_views.xml',
        'views/vehicle_brand.xml',
        'views/vehicle_type.xml',
        'views/vehicle_model.xml',
        'views/account_move.xml',
        'views/menuitems.xml',
        # 'data/templates/edi_document.xml',
         'data/templates/report_invoice.xml'
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}
