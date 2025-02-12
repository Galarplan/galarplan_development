# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

{
    "name": "Cancel Inventory Transfer | Delete Inventory Transfer",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "Warehouse",
    "license": "OPL-1",
    "summary": "Stock transfer Cancel Stock Picking Delete Stock Picking Delete Inventory Picking cancel done picking stock picking cancel pickings Reverse Stock Picking Revert Stock Picking cancel delivery order inventory transfer cancel Odoo",
    "description": """This module helps to cancel stock-pickings. You can also cancel multiple stock-pickings from the tree view. You can cancel the stock-pickings in 3 ways,

1) Cancel Only: When you cancel the stock-pickings then the stock-pickings are cancelled and the state is changed to "cancelled".
2) Cancel and Reset to Draft: When you cancel the stock-pickings, first stock-pickings are cancelled and then reset to the draft state.
3) Cancel and Delete: When you cancel the stock-pickings then first the stock-pickings are cancelled and then the stock-pickings will be deleted.""",
    "version": "16.0.1",
    "depends": [
                "stock",

    ],
    "application": True,
    "data": [
        'security/stock_security.xml',
        'data/server_action_data.xml',
        'views/res_config_settings_views.xml',
        'views/stock_picking_views.xml',
    ],
    "images": ["static/description/background.png", ],
    "auto_install": False,
    "installable": True,
    "price": 15,
    "currency": "EUR"
}
