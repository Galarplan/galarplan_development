{
    'name': 'Notas de Pedido',
    'version': '1.0',
    'category': 'Sales',
    'depends': ['base', 'account'],
    'data': [
        'security/note_order_groups.xml',
        'security/ir.model.access.csv',
        'views/note_order_views.xml',
    ],
    'installable': True,
    'application': True,
}
