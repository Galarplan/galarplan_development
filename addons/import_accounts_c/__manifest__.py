# -*- coding: utf-8 -*-
{
    'name': "import_accounts_c",

    'summary': """
        Import account to customers invoice""",

    'description': """
        Import account to customers invoice
    """,

    'author': "forestdbs",
    'website': "https://www.forestdbs.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'localization',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','l10n_ec'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/views.xml',
        # 'views/templates.xml',
        'data/l10n_latam_document_type_data.xml'
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}
