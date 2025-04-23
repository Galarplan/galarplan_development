from odoo import _, api, fields, models
from odoo.addons.l10n_ec.models.res_partner import PartnerIdTypeEc


class AccountMove(models.Model):
    _inherit = 'account.move'


    def _get_l10n_latam_documents_domain(self):
        self.ensure_one()
        domain = super()._get_l10n_latam_documents_domain()
        if self.country_code == 'EC' and self.journal_id.l10n_latam_use_documents:
            if self.debit_origin_id:  # show/hide the debit note document type
                domain.extend([('internal_type', '=', 'debit_note')])
            elif self.move_type == 'in_invoice':
                domain.extend([('internal_type', 'in', ['invoice', 'debit_note'])])
            elif self.move_type == 'out_invoice':
                domain.extend([('internal_type', '=', 'invoice')])    
            allowed_documents = self._get_l10n_ec_documents_allowed(PartnerIdTypeEc.get_ats_code_for_partner(self.partner_id, self.move_type))
            domain.extend([('id', 'in', allowed_documents.ids)])
        return domain