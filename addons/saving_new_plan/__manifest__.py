{
    'name': 'Planes de Ahorro - Descuento Especial',
    'version': '1.0',
    'description': 'Módulo para gestionar descuentos especiales en planes de ahorro.',
    'summary': 'Gestión de descuentos especiales en planes de ahorro',
    'author': 'Forestdbs',
    'website': 'https://www.tuempresa.com',
    'license': 'LGPL-3',
    'category': 'Accounting/Accounting',
    'depends': [
        'planes_ahorro',  # Dependencia del módulo principal de planes de ahorro
        'account',        # Dependencia de contabilidad
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_saving_line.xml',  # Vista del formulario
        'wizard/account_saving_discount_wizard_views.xml',
    ],
   
    'auto_install': False,
    'application': False,
    'installable': True,
}