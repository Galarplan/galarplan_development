from odoo import api, models, fields, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import format_date


import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    def _check_lock_date(self):
        """ Verificar fecha de bloqueo para movimientos en borrador """
        for move in self:
            if move.state == 'draft' and move.date:
                company = move.company_id
                lock_date = company._get_user_fiscal_lock_date()
                
                if fields.Date.to_date(move.date) <= lock_date:
                    raise ValidationError(
                        _("Cannot modify or create a draft entry with date %(date)s before the lock date %(lock_date)s. "
                          "Please contact your administrator.") % {
                            'date': format_date(self.env, move.date),
                            'lock_date': format_date(self.env, lock_date)
                        }
                    )

    def write(self, vals):
        # Verificar bloqueo antes de escribir
        if any(field in vals for field in ['date', 'state', 'line_ids', 'invoice_date', 'invoice_date_due']):
            self._check_lock_date()
        return super(AccountMove, self).write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        # Crear primero los movimientos
        moves = super(AccountMove, self).create(vals_list)
        # Luego verificar el bloqueo de fecha
        moves._check_lock_date()
        return moves

    def action_post(self):
        # Verificar al publicar un asiento con fecha bloqueada
        for move in self:
            if move.state == 'draft' and move.date:
                company = move.company_id
                lock_date = company._get_user_fiscal_lock_date()
                
                if fields.Date.to_date(move.date) <= lock_date:
                    raise ValidationError(
                        _("Cannot post entry with date %(date)s before the lock date %(lock_date)s. "
                          "Please change the date or contact your administrator.") % {
                            'date': format_date(self.env, move.date),
                            'lock_date': format_date(self.env, lock_date)
                        }
                    )
        return super(AccountMove, self).action_post()

    def button_draft(self):
        # Verificar al cambiar a borrador un asiento con fecha bloqueada
        res = super(AccountMove, self).button_draft()
        self._check_lock_date()
        return res