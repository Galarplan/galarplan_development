# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from json import dumps

from odoo import _, api, fields, models
from datetime import datetime,timedelta

class AccountMove(models.Model):
    _inherit = 'account.move'

    
    def button_cancel_to_draft(self):
        for brw_each in self:
            # Remueve la conciliación de las líneas contables
            brw_each.line_ids.remove_move_reconcile()
            
            # Cambia el estado a 'borrador' directamente sin llamar al método original
            brw_each.state = "draft"
            
        return True
    
    def button_cancel(self):
        for brw_each in self:
            brw_each.line_ids.remove_move_reconcile()
        values=super(AccountMove,self).button_cancel()
        for brw_each in self:
            if brw_each.state=="cancel":
                if brw_each.journal_id.l10n_ec_withhold_type=="in_withhold" or (brw_each.move_type in ("out_invoice","out_refund")):
                    if brw_each.edi_document_ids:
                        for brw_document in brw_each.edi_document_ids:
                            brw_each.anulado_sri=True
                if brw_each.journal_id.l10n_ec_withhold_type=="in_withhold" or (brw_each.move_type in ("out_invoice","out_refund")):
                    brw_each.edi_state="cancelled"
                    if brw_each.edi_document_ids:
                        brw_each.edi_document_ids.state = "cancelled"
        return values

    def button_cancel_invoice_and_withhold(self):
        for brw_each in self:
            # Remueve la conciliación de las líneas contables
            brw_each.line_ids.remove_move_reconcile()
            
            # Cambia el estado a 'borrador' directamente sin llamar al método original
            brw_each.state = "cancel"
            
        return True


    def button_publish_only_accounting(self):
      for move in self:
          if move.state == "draft":
              move.state = "posted"  # Cambiar el estado a "publicado" (posted)
              # Asegurarse de no afectar el estado de los documentos EDI asociados
      return True
    