{
    'name': 'Cambios en Pagos ',
    'version': '1.0',
    'category': 'Se realiza  cambios de modulos de pagos',
    'description': """

    """,
    'author': "Lajonner Crespin",
    'website': '',
    'depends': [
         'account_payment_advance',
    ],
    'data': [
         "security/res_groups.xml",
        "security/ir.model.access.csv",
        "wizard/account_prepayment_assignment.xml",
        "wizard/account_payment_cancel_wizard.xml",
        "views/account_payment.xml",
    ],
    'installable': True,
}
