{
    'name': 'Customer Attention',
    'version': '1.0',
    'summary': 'Module for managing customer attention processes',
    'description': """
        This module handles customer attention, devolutions and related documents.
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'category': 'Customer Relationship Management',
    'depends': ['base', 'hr', 'account', 'planes_ahorro'],
    'data': [
        'security/customer_attention_groups.xml',
        'security/ir.model.access.csv',
        'views/attention_concept_views.xml',
        'views/attention_user_views.xml',
        'views/attention_devolution_views.xml',
        'views/document_attention_views.xml',
        'views/document_reason_views.xml',
        'views/document_action_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}