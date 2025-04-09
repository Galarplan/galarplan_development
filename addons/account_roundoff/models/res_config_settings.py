from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    invoice_roundoff = fields.Boolean(
        string='Allow rounding of invoice amount',
        config_parameter='account.invoice_roundoff',
        help="Allow rounding of invoice amount"
    )
    roundoff_account_id = fields.Many2one(
        'account.account',
        string='Roundoff Account',
        config_parameter='account.roundoff_account_id',
        help="Account to post rounding differences",
    )
