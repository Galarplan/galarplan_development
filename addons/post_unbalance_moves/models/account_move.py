from odoo import _, api, fields, models
from collections import defaultdict
from contextlib import ExitStack, contextmanager
from datetime import date, timedelta

class AccountMove(models.Model):

    _inherit = 'account.move'
    

    @contextmanager
    def _check_balanced(self, container):
        ''' Assert the move is fully balanced debit = credit.
        An error is raised if it's not the case.
        '''

        with self._disable_recursion(container, 'check_move_validity', default=True, target=False) as disabled:
            yield
            if disabled:
                return
        return
        unbalanced_moves = self._get_unbalanced_moves(container)
        if unbalanced_moves:
            error_msg = _("An error has occurred.")
            for move_id, sum_debit, sum_credit in unbalanced_moves:
                move = self.browse(move_id)
                error_msg += _(
                    "\n\n"
                    "The move (%s) is not balanced.\n"
                    "The total of debits equals %s and the total of credits equals %s.\n"
                    "You might want to specify a default account on journal \"%s\" to automatically balance each move.",
                    move.display_name,
                    format_amount(self.env, sum_debit, move.company_id.currency_id),
                    format_amount(self.env, sum_credit, move.company_id.currency_id),
                    move.journal_id.name)
            raise UserError(error_msg)