# -*- coding: utf-8 -*-
{
    "name": "Reporte financieros por Vistas",
    "version": "16.0.0.0.1",
    "category": "Reporte financieros",
    "license": "AGPL-3",
    "summary": "Reporte financieros",
    "author": "Lajonner Crespin,David Crespin",
    "depends": ["base", "account", "report_xlsx"],
    "data": [
        #
        "security/ir.model.access.csv",
        #
        'reports/report_view_general_ledger.xml',
        'reports/ir_actions_report_xml.xml',
        ####
        "views/report_view_general_ledger_line.xml",
        "views/report_view_general_ledger.xml",
        #
        "views/ir_ui_menu.xml"
        #
    ],
    "demo": [],
    "installable": True,
}
