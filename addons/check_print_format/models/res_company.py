# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = "res.company"

    account_check_printing_layout = fields.Selection(
        selection_add=[
            ("custom_melacorp_bank", "Custom Galarplan"),
            ("check_print_format.report_custom_check_action", "Formato de cheque Galarplan"),
        ],
        ondelete={
            "custom_melacorp_bank": "set default",
        },
    )

    # account_check_printing_date_label = fields.Boolean(default=True)
    # account_check_printing_multi_stub = fields.Boolean()
    # account_check_printing_margin_top = fields.Float(default=0.25)
    # account_check_printing_margin_left = fields.Float(default=0.25)
    # account_check_printing_margin_right = fields.Float(default=0.25)

    # @api.model
    # def _get_check_layouts(self):
    #     return []
