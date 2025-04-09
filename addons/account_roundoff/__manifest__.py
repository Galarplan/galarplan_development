{
    "name": "Redondeo de facturas",
    "version": "1.0",
    "author": "Anthony Villacis.",
    "sequence": 110,
    "category": "Account",
    "website": "http://www.forestdbs.com",
    "license": "LGPL-3",
    "support": "soporte@forestdbs.com",
    "description": """ 
        Este módulo gestiona el redondeo del valor en el importe total del presupuesto, la orden de compra y la factura (ventas y compras).
        Después de instalar este módulo, en Ajustes -> Configuración -> Contabilidad se habilita un campo para la cuenta de redondeo por defecto. Esto debe ser asignado para obtener el valor redondeado en los libros financieros.
    """,
    "depends": ["base", "account", "sale", "purchase"],
    "data": [
        'views/res_config_setting.xml',
        'views/account_move.xml'
        # "views/sale_view.xml",
        # "views/purchase_view.xml",
        # "views/account_config_view.xml",
    ],
    # "images": ["static/description/banner.png"],
    "installable": True,
    "application": True,
}
