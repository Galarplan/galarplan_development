from odoo import _, api, fields, models
from odoo.addons.l10n_ec.models.res_partner import PartnerIdTypeEc


class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_latam_available_document_type_ids = fields.Many2many(
        'l10n_latam.document.type',
        compute='_compute_l10n_latam_available_document_types_2'
    )

    # @api.depends('journal_id', 'partner_id', 'company_id', 'move_type')
    # def _compute_l10n_latam_available_document_types_2(self):
    #     DocumentType = self.env['l10n_latam.document.type']
    #     self.l10n_latam_available_document_type_ids = False
    #     for rec in self.filtered(lambda x: x.journal_id and x.l10n_latam_use_documents and x.partner_id):
    #         print('======= Dominio generado:')
    #         domain = rec._get_l10n_latam_documents_domain()
    #         print(domain)
    #         rec.l10n_latam_available_document_type_ids = DocumentType.search(domain)

    @api.depends('journal_id', 'partner_id', 'company_id', 'move_type')
    def _compute_l10n_latam_available_document_types_2(self):
        DocumentType = self.env['l10n_latam.document.type']
        for rec in self:
            if rec.journal_id and rec.journal_id.l10n_latam_use_documents:
                rec.l10n_latam_available_document_type_ids = DocumentType.search([
                    ('country_id', '=', rec.company_id.country_id.id)
                ])
            else:
                rec.l10n_latam_available_document_type_ids = False

    def _get_l10n_latam_documents_domain(self):
        self.ensure_one()
        domain = super()._get_l10n_latam_documents_domain()
        print('======= Llegó a _get_l10n_latam_documents_domain')

        if self.country_code == 'EC' and self.journal_id.l10n_latam_use_documents:
            internal_types = []

            if self.debit_origin_id:
                internal_types = ['debit_note']
            elif self.move_type == 'in_invoice':
                internal_types = ['invoice', 'debit_note'] 
            elif self.move_type == 'out_invoice':
                internal_types = ['invoice']

            if internal_types:
                domain.append(('internal_type', 'in', internal_types))

            allowed_documents = self._get_l10n_ec_documents_allowed(
                PartnerIdTypeEc.get_ats_code_for_partner(self.partner_id, self.move_type)
            )

            domain.append(('id', 'in', allowed_documents.ids))
            print('======= Dominio final limpio:', domain)

        return domain
