from odoo import models, fields, api, _
from odoo.exceptions import RedirectWarning


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def do_print_checks(self):
        check_layout = self.company_id.account_check_printing_layout
        redirect_action = self.env.ref('account.action_account_config')
        print("check_layout======================", check_layout)
        if not check_layout or check_layout == 'disabled':
            msg = _("You have to choose a check layout. For this, go in Invoicing/Accounting Settings, search for 'Checks layout' and set one.")
            raise RedirectWarning(msg, redirect_action.id, _('Go to the configuration panel'))
        report_action = self.env.ref(check_layout, False)
        print("report_action======================", report_action)
        if not report_action:
            msg = _("Something went wrong with Check Layout, please select another layout in Invoicing/Accounting Settings and try again.")
            raise RedirectWarning(msg, redirect_action.id, _('Go to the configuration panel'))
        self.write({'is_move_sent': True})
        return report_action.report_action(self)
