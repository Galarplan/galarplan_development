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
    total_accumulated = fields.Float(
        string="Total Acumulado",
        compute='_compute_total_accumulated',
        store=True,
        readonly=True
    )

    @api.depends('line_ids.amount_accumulated')
    def _compute_total_accumulated(self):
        for report in self:
            if report.line_ids:
                report.total_accumulated = report.line_ids[-1].amount_accumulated  # Último valor acumulado
            else:
                report.total_accumulated = 0.0
                
    # journal_ids = fields.Many2many('account.journal',
    #                                'account_report_general_ledger_view_journal_rel',
    #                                'account_id', 'journal_id',
    #                                string='Journals', required=True)
    line_ids = fields.One2many('report.view.general.ledger.line', 'report_id', string='Lines', readonly=True)

    # def action_process_init_sql(self, date_start, date_end):
    #     for each in self:
    #         if not date_start:
    #             date_start = '1990-01-01'
    #         company_id = each.company_id.id
    #         account_id = each.account_id.id
    #         partner_id = each.partner_id.id
    #         journal_id = each.journal_id and each.journal_id.id or 0
    #         filter_state = each.target_move
    #         # sort_By = (each.sortby == "sort_date" and " order by coalesce(l.date_maturity,am.date) asc" or " order by aj.name asc ")
    #         self._cr.execute(f"""WITH variables AS (
    #         SELECT 
    #             {company_id}::int AS company_id,
    #             {account_id}::int AS account_id,
    #             {partner_id}::int AS partner_id,
    #             {journal_id}::int AS journal_id,
    #             '{date_start}'::date AS date_start,
    #             '{date_end}'::date AS date_end,
    #             '{filter_state}'::varchar AS filter_state
    #             )
        
    #             SELECT 
    #                 SUM(l.debit - l.credit) AS balance
    #             FROM account_move am 
    #             inner join account_journal aj on aj.id=am.journal_id 
    #             INNER JOIN account_move_line l ON l.move_id = am.id
    #             INNER JOIN variables ON am.company_id = variables.company_id  
    #             WHERE 
    #                 (am.date < variables.date_end)
    #                 AND (
    #                     variables.filter_state = 'all' 
    #                     OR (variables.filter_state = 'posted' AND am.state = 'posted')
    #                 )
    #                 AND (variables.account_id = 0 OR l.account_id = variables.account_id)
    #                 AND (variables.partner_id = 0 OR l.partner_id = variables.partner_id)
    #                 AND (variables.journal_id = 0 OR am.journal_id = variables.journal_id)
    #         """)
    #         accounts_res = self._cr.dictfetchall()
    #         return accounts_res

    # def action_process_sql(self):
    #     for each in self:
    #         company_id = each.company_id.id
    #         account_id = each.account_id.id
    #         partner_id = each.partner_id.id
    #         journal_id = each.journal_id and each.journal_id.id or 0
    #         date_start = each.date_from
    #         date_end = each.date_to
    #         filter_state = each.target_move

    #         sort_By = (each.sortby == "sort_date" and " order by coalesce(l.date_maturity,am.date) asc" or " order by aj.name asc ")
    #         self._cr.execute(f"""WITH variables AS (
    #         SELECT 
    #             {company_id}::int AS company_id,
    #             {account_id}::int AS account_id,
    #             {partner_id}::int AS partner_id,
    #             {journal_id}::int AS journal_id,
    #             '{date_start}'::date AS date_start,
    #             '{date_end}'::date AS date_end,
    #             '{filter_state}'::varchar AS filter_state
    #             )

    #             SELECT 
    #                 l.id AS move_line_id,
    #                 am.id as move_id,
    #                 l.company_id,
    #                 l.partner_id,
    #                 l.ref AS referencia,
    #                 am.name as lname,
    #                 l.debit AS debit,
    #                 l.credit AS credit,
    #                 (l.debit - l.credit) AS balance,
    #                 coalesce(l.date_maturity,am.date) as ldate,
    #                 aj.id as journal_id 
    #             FROM account_move am 
    #             inner join account_journal aj on aj.id=am.journal_id 
    #             INNER JOIN account_move_line l ON l.move_id = am.id
    #             INNER JOIN variables ON am.company_id = variables.company_id  
    #             WHERE 
    #                 (am.date BETWEEN variables.date_start AND variables.date_end)
    #                 AND (
    #                     variables.filter_state = 'all' 
    #                     OR (variables.filter_state = 'posted' AND am.state = 'posted')
    #                 )
    #                 AND (variables.account_id = 0 OR l.account_id = variables.account_id)
    #                 AND (variables.partner_id = 0 OR l.partner_id = variables.partner_id)
    #                 AND (variables.journal_id = 0 OR am.journal_id = variables.journal_id)
    #             {sort_By}
    #         """)
    #         accounts_res = self._cr.dictfetchall()
    #         return accounts_res
    def action_process_init_sql(self, date_start, date_end):
        self.ensure_one()
        if not date_start:
            date_start = '1990-01-01'
        
        query = """
            SELECT 
                SUM(l.debit - l.credit) AS balance
            FROM account_move_line l
            JOIN account_move am ON l.move_id = am.id
            JOIN account_journal aj ON am.journal_id = aj.id
            WHERE am.company_id = %s
            AND am.date < %s
            AND (%s = 'all' OR (%s = 'posted' AND am.state = 'posted'))
            AND (%s = 0 OR l.account_id = %s)
            AND (%s = 0 OR l.partner_id = %s)
            AND (%s = 0 OR am.journal_id = %s)
        """
        params = (
            self.company_id.id,
            date_end,
            self.target_move, self.target_move,
            0 if not self.account_id else self.account_id.id,
            0 if not self.account_id else self.account_id.id,
            0 if not self.partner_id else self.partner_id.id,
            0 if not self.partner_id else self.partner_id.id,
            0 if not self.journal_id else self.journal_id.id,
            0 if not self.journal_id else self.journal_id.id,
        )
        
        self._cr.execute(query, params)
        return self._cr.dictfetchall()

    def action_process_sql(self):
        self.ensure_one()
        sort_order = "coalesce(l.date_maturity, am.date)" if self.sortby == "sort_date" else "aj.name"
        
        query = f"""
            SELECT 
                l.id AS move_line_id,
                am.id as move_id,
                l.company_id,
                l.partner_id,
                l.ref AS referencia,
                am.name as lname,
                l.debit AS debit,
                l.credit AS credit,
                (l.debit - l.credit) AS balance,
                coalesce(l.date_maturity, am.date) as ldate,
                aj.id as journal_id 
            FROM account_move_line l
            JOIN account_move am ON l.move_id = am.id
            JOIN account_journal aj ON am.journal_id = aj.id
            WHERE am.company_id = %s
            AND am.date BETWEEN %s AND %s
            AND (%s = 'all' OR (%s = 'posted' AND am.state = 'posted'))
            AND (%s = 0 OR l.account_id = %s)
            AND (%s = 0 OR l.partner_id = %s)
            AND (%s = 0 OR am.journal_id = %s)
            ORDER BY {sort_order}
        """
        params = (
            self.company_id.id,
            self.date_from,
            self.date_to,
            self.target_move, self.target_move,
            0 if not self.account_id else self.account_id.id,
            0 if not self.account_id else self.account_id.id,
            0 if not self.partner_id else self.partner_id.id,
            0 if not self.partner_id else self.partner_id.id,
            0 if not self.journal_id else self.journal_id.id,
            0 if not self.journal_id else self.journal_id.id,
        )
        
        self._cr.execute(query, params)
        return self._cr.dictfetchall()

    def action_process(self):
        for report in self:
            # Limpiar líneas existentes de manera eficiente
            report.line_ids.unlink()
            
            accounts_res = report.action_process_sql()
            if not accounts_res:
                continue
                
            # Pre-cargar datos relacionados para evitar N+1 queries
            move_line_ids = [res['move_line_id'] for res in accounts_res if res.get('move_line_id')]
            move_lines = self.env['account.move.line'].browse(move_line_ids)
            move_line_data = {ml.id: ml.move_id.id for ml in move_lines}
            
            balance = 0.00
            DEC = 2
            lines_to_create = []
            
            for move in accounts_res:
                balance += move.get('balance', 0.0)
                lines_to_create.append({
                    'date': move.get('ldate'),
                    'partner_id': move.get('partner_id'),
                    'name': move.get('lname') or '',
                    'journal_id': move.get('journal_id'),
                    'debit': move.get('debit', 0.0),
                    'credit': move.get('credit', 0.0),
                    'amount_accumulated': round(balance, DEC),
                    'move_id': move_line_data.get(move.get('move_line_id')),
                    'report_id': report.id,
                })
                
                # Crear en lotes para mejorar rendimiento
                if len(lines_to_create) >= 100:
                    self.env['report.view.general.ledger.line'].create(lines_to_create)
                    lines_to_create = []
            
            # Crear las líneas restantes
            if lines_to_create:
                self.env['report.view.general.ledger.line'].create(lines_to_create)
        
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
