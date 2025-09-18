from odoo import api, models, fields, _
from odoo.exceptions import ValidationError
from odoo.tools import format_date

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def write(self, vals):
        # Verificar bloqueo al modificar líneas de asiento
        if any(field in vals for field in ['debit', 'credit', 'account_id', 'date', 'amount_currency']):
            for line in self:
                if line.move_id.state == 'draft' and line.date:
                    company = line.move_id.company_id
                    lock_date = company._get_user_fiscal_lock_date()
                    
                    if fields.Date.to_date(line.date) <= lock_date:
                        raise ValidationError(
                            _("Cannot modify line of draft entry with date %(date)s before the lock date %(lock_date)s.") % {
                                'date': format_date(self.env, line.date),
                                'lock_date': format_date(self.env, lock_date)
                            }
                        )
        return super(AccountMoveLine, self).write(vals)