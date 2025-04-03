from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    state = fields.Selection(
        selection_add=[('migrado', 'odoo14')],
        ondelete={'migrado': lambda records: records.write({'state': 'draft'})}
    )
