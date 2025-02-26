# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name": "Import Multiple Journal Entries from CSV File | Import Multiple Journal Entries from Excel file",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "Accounting",
    "summary": "Import Journal Entries From CSV Import Journal Entries From Excel Import Journal Entry From CSV import Journal Entry From Excel Import Mass Journal Import Multiple Journal import account move import opening journal import opening balance Odoo",
    "description": """This module is used to import multiple journal entries from CSV/Excel files. We provide the option to import analytic tags and all related to analytic accounts with journal entries. You can import multiple entries in a single click!""",
    "version": "16.0.3",
    "depends": [
        "sh_message",
        "account",
    ],
    "application": True,
    "data": [
        "security/import_journal_entry_security.xml",
        "security/ir.model.access.csv",
        "wizard/import_journal_entry_wizard_views.xml",
    ],
    'external_dependencies': {
        'python': ['xlrd'],
    },
    "images": ["static/description/background.png", ],
    "license": "OPL-1",
    "auto_install": False,
    "installable": True,
    "price": "13",
    "currency": "EUR"
}
