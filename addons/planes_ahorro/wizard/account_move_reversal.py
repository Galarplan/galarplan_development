from odoo import models, fields, api,_
from odoo.exceptions import ValidationError


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    @api.model
    def _get_default_document_type_id(self):
        srch = self.env["l10n_latam.document.type"].sudo().search([('code', '=', '04')])
        return srch and srch[0].id or False

    def _reverse_moves(self,default_values_list, cancel=False):
        moves=super(AccountMoveReversal,self)._reverse_moves(default_values_list, cancel=cancel)
        return moves

    def reverse_moves(self):
        values=super(AccountMoveReversal,self).reverse_moves()
        if type(values)==dict:
            if values.get("res_model","")=="account.move":
                if "res_id" in values:
                    brw_move=self.env["account.move"].browse(values["res_id"])
                    if brw_move.move_type in ('out_refund','in_refund') and brw_move.state=='draft':
                        brw_move.l10n_latam_document_type_id=self._get_default_document_type_id()
                        if brw_move.reversed_entry_id:
                            brw_move.manual_document_number=brw_move.reversed_entry_id.l10n_latam_document_number
                            brw_move.manual_date = brw_move.reversed_entry_id.invoice_date or brw_move.reversed_entry_id.date
                            brw_move.manual_origin_authorization = brw_move.reversed_entry_id.l10n_ec_authorization_number
                else:
                    domain=values.get("domain",[])
                    if domain[0][2]:#ids
                        brw_move = self.env["account.move"].browse(values["res_id"])
                        if brw_move.move_type in ('out_refund','in_refund') and brw_move.state == 'draft':
                            brw_move.l10n_latam_document_type_id = self._get_default_document_type_id()
                            brw_move.manual_document_number = brw_move.reversed_entry_id.l10n_latam_document_number
                            brw_move.manual_date = brw_move.reversed_entry_id.invoice_date or brw_move.reversed_entry_id.date
                            brw_move.manual_origin_authorization = brw_move.reversed_entry_id.l10n_ec_authorization_number
        return values

