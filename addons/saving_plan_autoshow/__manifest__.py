{
    'name': 'Plan autoshow',
    'version': '1.0',
    'description': 'Planes especiales para autoshow',
    'summary': 'Planes especiales para autoshow',
    'author': 'Forestdbs',
    'website': 'www.forestdbs.com',
    'license': 'LGPL-3',
    'category': 'account',
    'depends': [
        'planes_ahorro',
        'saving_new_plan',
        'fithy_plus_one',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_saving.xml',
        'views/account_saving_plan.xml',
        'views/ir_ui_menu.xml'
    ],
    'auto_install': False,
    'application': False,
}