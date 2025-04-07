# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import UserError, ValidationError


class report_view_general_ledger(models.Model):
    _name = 'report.view.general.ledger'
    _description = 'Reporte Mayor'

    @api.depends('account_id', 'partner_id')
    def _compute_name(self):
        ref_name = ''
        for record in self:
            if record.account_id:
                ref_name += record.account_id and record.account_id.code or ''
            if record.partner_id:
                ref_name += record.partner_id and record.partner_id.name or ''
            record.name = ref_name

    name = fields.Char(string="Name", compute='_compute_name')
    company_id = fields.Many2one('res.company', string='Compañia', required=True, readonly=True, default=lambda self: self.env.company)
    date_from = fields.Date(string='Fecha de inicio', required=True,
                            default=lambda self: fields.Date.to_string(date.today().replace(day=1)))
    date_to = fields.Date(string='Fecha final', required=True,
                          default=lambda self: fields.Date.to_string(date.today()))
    account_analytic_id = fields.Many2one('account.analytic.account', string='Cuenta analitica')
    partner_id = fields.Many2one('res.partner', string='Empresa')
    account_id = fields.Many2one('account.account', string='Cuenta')
    journal_id = fields.Many2one('account.journal', string='Diario')
    # analytic_account_ids = fields.Many2many('account.analytic.account',
    #                                        string='Analytic Accounts')
    # partner_ids = fields.Many2many('res.partner', string='Partners')
    target_move = fields.Selection([('posted', 'Publicadas'),
                                    ('all', 'Todos'),
                                    ], string='Estado', required=True, default='posted')
    sortby = fields.Selection([('sort_date', 'Fecha'),
                               ('sort_journal_partner', 'Diario')],
                              string='Ordenar por', required=True, default='sort_date')
    currency_id = fields.Many2one('res.currency', string='Moneda', related='company_id.currency_id')
    initial_balance = fields.Boolean(string='Incluir saldos iniciales',
                                     help='If you selected date, this field allow'
                                          ' you to add a row to display the amount '
                                          'of debit/credit/balance that precedes'
                                          ' the filter you\'ve set.')
    # journal_ids = fields.Many2many('account.journal',
    #                                'account_report_general_ledger_view_journal_rel',
    #                                'account_id', 'journal_id',
    #                                string='Journals', required=True)
    line_ids = fields.One2many('report.view.general.ledger.line', 'report_id', string='Lines', readonly=True)

    def action_process_init_sql(self, date_start, date_end):
        for each in self:
            if not date_start:
                date_start = '1990-01-01'
            company_id = each.company_id.id
            account_id = each.account_id.id
            partner_id = each.partner_id.id
            journal_id = each.journal_id and each.journal_id.id or 0
            filter_state = each.target_move
            # sort_By = (each.sortby == "sort_date" and " order by coalesce(l.date_maturity,am.date) asc" or " order by aj.name asc ")
            self._cr.execute(f"""WITH variables AS (
            SELECT 
                {company_id}::int AS company_id,
                {account_id}::int AS account_id,
                {partner_id}::int AS partner_id,
                {journal_id}::int AS journal_id,
                '{date_start}'::date AS date_start,
                '{date_end}'::date AS date_end,
                '{filter_state}'::varchar AS filter_state
                )
        
                SELECT 
                    SUM(l.debit - l.credit) AS balance
                FROM account_move am 
                inner join account_journal aj on aj.id=am.journal_id 
                INNER JOIN account_move_line l ON l.move_id = am.id
                INNER JOIN variables ON am.company_id = variables.company_id  
                WHERE 
                    (am.date < variables.date_end)
                    AND (
                        variables.filter_state = 'all' 
                        OR (variables.filter_state = 'posted' AND am.state = 'posted')
                    )
                    AND (variables.account_id = 0 OR l.account_id = variables.account_id)
                    AND (variables.partner_id = 0 OR l.partner_id = variables.partner_id)
                    AND (variables.journal_id = 0 OR am.journal_id = variables.journal_id)
            """)
            accounts_res = self._cr.dictfetchall()
            return accounts_res

    def action_process_sql(self):
        for each in self:
            company_id = each.company_id.id
            account_id = each.account_id.id
            partner_id = each.partner_id.id
            journal_id = each.journal_id and each.journal_id.id or 0
            date_start = each.date_from
            date_end = each.date_to
            filter_state = each.target_move

            sort_By = (each.sortby == "sort_date" and " order by coalesce(l.date_maturity,am.date) asc" or " order by aj.name asc ")
            self._cr.execute(f"""WITH variables AS (
            SELECT 
                {company_id}::int AS company_id,
                {account_id}::int AS account_id,
                {partner_id}::int AS partner_id,
                {journal_id}::int AS journal_id,
                '{date_start}'::date AS date_start,
                '{date_end}'::date AS date_end,
                '{filter_state}'::varchar AS filter_state
                )

                SELECT 
                    l.id AS move_line_id,
                    l.company_id,
                    l.partner_id,
                    l.ref AS referencia,
                    am.name as lname,
                    l.debit AS debit,
                    l.credit AS credit,
                    (l.debit - l.credit) AS balance,
                    coalesce(l.date_maturity,am.date) as ldate,
                    aj.id as journal_id 
                FROM account_move am 
                inner join account_journal aj on aj.id=am.journal_id 
                INNER JOIN account_move_line l ON l.move_id = am.id
                INNER JOIN variables ON am.company_id = variables.company_id  
                WHERE 
                    (am.date BETWEEN variables.date_start AND variables.date_end)
                    AND (
                        variables.filter_state = 'all' 
                        OR (variables.filter_state = 'posted' AND am.state = 'posted')
                    )
                    AND (variables.account_id = 0 OR l.account_id = variables.account_id)
                    AND (variables.partner_id = 0 OR l.partner_id = variables.partner_id)
                    AND (variables.journal_id = 0 OR am.journal_id = variables.journal_id)
                {sort_By}
            """)
            accounts_res = self._cr.dictfetchall()
            return accounts_res

    def action_process(self):
        for each in self:
            accounts_res = each.action_process_sql()
            lines_move = [(5,)]
            balance = 0.00
            DEC = 2
            for move in accounts_res:
                # Iterar sobre la lista de 'move_lines'
                balance += move.get('balance')
                lines_move.append((0, 0, {'date': move.get('ldate'),
                                          'partner_id': move.get('partner_id', None),
                                          'name': move.get('lname'),
                                          'journal_id': move.get('journal_id', None),
                                          'debit': move.get('debit'),
                                          'credit': move.get('credit'),
                                          'amount_accumulated': round(balance, DEC)
                                          }))
                each.write({'line_ids': lines_move})
        return True

    def print_general_ledger(self):
        return self.env.ref('report_financial_view_accountant.report_general_ledger').report_action(self)

    def action_export_excel(self):
        return self.env.ref('report_financial_view_accountant.action_general_ledger_xlsx').report_action(self)

    def pre_print_reportfile(self):
        # def add_months(sourcedate, months):
        #     month = sourcedate.month - 1 + months
        #     year = sourcedate.year + month // 12
        #     month = month % 12 + 1
        #     day = min(sourcedate.day, calendar.monthrange(year, month)[1])
        #     return datetime.date(year, month, day)

        # date_begin = add_months(datetime.datetime.strptime(self.date, "%Y-%m-%d"), -1).strftime("%Y-%m-%d")  # , %H:%M:%S
        # date_begin = add_months(fields.Date.from_string(self.date), -1).strftime("%Y-%m-%d")
        datas = {}
        datas['ids'] = self.ids
        # data['date_real_start'] = date_begin
        # data['date_start'] = str(self.date)
        # data['date_end'] = str(self.date_end)
        # data['sel_position'] = self.sel_position
        # data['user_id'] = self.user_id and ' =' + str(self.user_id.id) or '<> 0'
        return datas
