from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

class ResUsers(models.Model):
    _inherit = 'res.users'

    password_receipt = fields.Char(
        string='Password Receipt',
        help='Receipt or confirmation of password change',
        copy=False,
        readonly=True,
    )
    
    def authenticate_receipt(self, db, login, password):
        """Authenticate user by login and receipt password."""
        user = self.search([('login', '=', login)], limit=1)
        if user and user.password_receipt and user.password_receipt == password:
            return user.id
        return False
    
    