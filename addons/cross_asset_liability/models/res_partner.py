from odoo import _, api, fields, models

class ResPartner(models.Model):
    
    _inherit = 'res.partner'
    
    @api.depends_context('company')
    def _credit_debit_get(self):
        if not self.ids:
            self.debit = False
            self.credit = False
            return
        tables, where_clause, where_params = self.env['account.move.line']._where_calc([
            ('parent_state', '=', 'posted'),
            ('company_id', '=', self.env.company.id)
        ]).get_sql()

        where_params = [tuple(self.ids)] + where_params
        if where_clause:
            where_clause = 'AND ' + where_clause
        self._cr.execute("""SELECT account_move_line.partner_id, a.account_type, SUM(account_move_line.amount_residual)
                      FROM """ + tables + """
                      LEFT JOIN account_account a ON (account_move_line.account_id=a.id)
                      WHERE a.account_type IN ('asset_receivable','liability_payable')
                      AND account_move_line.partner_id IN %s
                      AND account_move_line.reconciled IS NOT TRUE
                      """ + where_clause + """
                      GROUP BY account_move_line.partner_id, a.account_type
                      """, where_params)
        treated = self.browse()
        for pid, type, val in self._cr.fetchall():
            partner = self.browse(pid)
            if type == 'asset_receivable':
                partner.credit = val or 0
                if partner not in treated:
                    partner.debit = False
                    treated |= partner
            elif type == 'liability_payable':
                partner.debit = -(val or 0)
                if partner not in treated:
                    partner.credit = False
                    treated |= partner
        remaining = (self - treated)
        remaining.debit = False
        remaining.credit = False