from odoo import models, api, fields

class AccountMove(models.Model):
    _inherit = "account.move"

    def get_journal_entries_data(self):
        """Retorna los apuntes contables relacionados con el asiento.
        Si es una factura de proveedor (in_invoice) con retenciones asociadas, 
        añade los apuntes contables de la retención publicada."""
        self.ensure_one()  # Asegura que solo se está ejecutando para un registro
        
        move_lines = []
        budget_lines = []
        withhold_name = ""
        
        # Consulta los apuntes contables del movimiento actual
        query = f"""
            SELECT 
                aml.id AS line_id,
                aa.code AS account_code,
                aa.name AS account_name,
                aml.debit,
                aml.credit,
                (aml.debit - aml.credit) AS balance,
                aml.ref AS reference,
                aj.name AS journal_name
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            JOIN account_journal aj ON aml.journal_id = aj.id
            WHERE aml.move_id = {self.id} order by account_code asc
        """
        self.env.cr.execute(query)
        move_lines.extend(self.env.cr.dictfetchall())
        
        # Si es una factura de proveedor (in_invoice), verificar retenciones asociadas
        # if self.move_type == 'in_invoice' and self.l10n_ec_withhold_count > 0:
        #     withhold_moves = self.env['account.move'].browse(self.l10n_ec_withhold_ids.ids)
            
        #     # Filtrar la retención publicada (estado 'posted')
        #     published_withhold = withhold_moves.filtered(lambda w: w.state == 'posted')
        #     withhold_name = published_withhold.name
        #     if published_withhold:
        #         for withhold in published_withhold:
        #             query_withhold = f"""
        #                 SELECT 
        #                     aml.id AS line_id,
        #                     aa.code AS account_code,
        #                     aa.name AS account_name,
        #                     aml.debit,
        #                     aml.credit,
        #                     (aml.debit - aml.credit) AS balance,
        #                     aml.ref AS reference,
        #                     aj.name AS journal_name
        #                 FROM account_move_line aml
        #                 JOIN account_account aa ON aml.account_id = aa.id
        #                 JOIN account_journal aj ON aml.journal_id = aj.id
        #                 WHERE aml.move_id = {withhold.id}
        #             """
        #             self.env.cr.execute(query_withhold)
        #             move_lines.extend(self.env.cr.dictfetchall())
        
        # Obtener los ítems presupuestarios relacionados
        # query_budget = f"""
        #     SELECT 
        #         bil.id AS budget_line_id,
        #         CONCAT(bi.code,' ',bi.name) AS budget_item_name,
        #         bil.amount,
        #         bil.amount_compromise,
        #         bil.amount_accrued
        #     FROM budget_item_line bil
        #     JOIN budget_transaction_line btl ON bil.budget_item = btl.id
        #     JOIN budget_item bi ON btl.item_id = bi.id
        #     WHERE bil.move_id = {self.id}
        # """
        # self.env.cr.execute(query_budget)
        # budget_lines.extend(self.env.cr.dictfetchall())
        
        return {
            'move_name': self.name,
            # 'withold_name': withhold_name,
            'move_date': self.date,
            'lines': move_lines
            # 'budget_lines': budget_lines
        }  

