# -*- coding: utf-8 -*-
{
    'name': "Reporte UAFE",

    'summary': """
        Reporte Uafe """,

    'description': """
        Reporte Uafe
    """,

    'author': "Forestdbs",
    'website': "https://www.forestdbs.com.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/res_company.xml',
        'views/res_country.xml',
        'views/res_partner.xml',
        'views/economy_activity.xml',
        'wizard/uafe_report.xml',
        'views/menuitems.xml',
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}
