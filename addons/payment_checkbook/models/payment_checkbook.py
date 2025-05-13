from odoo import models, fields, api
from odoo.exceptions import UserError
import json

class Checkbook(models.Model):
    _name = 'payment.checkbook'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Checkbook'

    journal_id = fields.Many2one('account.journal', required=True)
    available_journals_ids = fields.Many2many(
    'account.journal',
    compute='_compute_available_journals'
    )
    bank_account_id = fields.Many2one('res.partner.bank', readonly=True)
    reference = fields.Char()
    date = fields.Date()
    return_date = fields.Date()
    from_seq = fields.Integer(required=True)
    to_seq = fields.Integer(required=True)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user, readonly=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='journal_id.currency_id', readonly=True)
    deferred_account_id = fields.Many2one('account.account')
    padding = fields.Integer(default=6)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('cancelled', 'Cancelled'),
    ], default='draft')

    checks_ids = fields.One2many('payment.checkbook.line', 'checkbook_id', string='Checks')


    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('processing', 'Processing'),
        ('missing', 'Missing'),
        ('cancelled', 'Cancelled')
    ], default='draft', string="Status")

    @api.depends('company_id')
    def _compute_available_journals(self):
        for record in self:
            domain = [
                ('type', '=', 'bank'),
                ('company_id', '=', record.company_id.id) if record.company_id else (),
                ('code', '!=', 'odo14')
            ]
            record.available_journals_ids = self.env['account.journal'].search(domain)

    # Métodos de cambio de estado
    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_open(self):
        for rec in self:
            rec.state = 'open'

    def action_process(self):
        for rec in self:
            rec.state = 'processing'

    def action_missing(self):
        for rec in self:
            rec.state = 'missing'

    def action_cancelled(self):
        for rec in self:
            rec.state = 'cancelled'
    
    def action_open(self):
        for rec in self:
            if not rec.checks_ids:
                seq_range = range(rec.from_seq, rec.to_seq + 1)
                for number in seq_range:
                    padded = str(number).zfill(rec.padding or 6)
                    self.env['payment.checkbook.line'].create({
                        'checkbook_id': rec.id,
                        'check_number': padded,
                        'journal_id': rec.journal_id.id
                    })
            rec.state = 'open'

    def name_get(self):
        result = []
        for rec in self:
            name = f"{rec.journal_id.name} / {rec.from_seq} - {rec.to_seq}"
            result.append((rec.id, name))
        return result
    

class CheckbookLine(models.Model):
    _name = 'payment.checkbook.line'
    _description = 'Check Line'

    checkbook_id = fields.Many2one('payment.checkbook', required=True, ondelete='cascade')
    check_number = fields.Char(string="Check Number", required=True)
    is_used = fields.Boolean(default=False)
    parent_state = fields.Selection(related='checkbook_id.state', store=True)
    reference = fields.Char('Reference')
    payment_id = fields.Many2one('account.payment', string='Used in Payment', readonly=True)
    journal_id = fields.Many2one('account.journal',string='Diario',readonly=True)

    def name_get(self):
        result = []
        for rec in self:
            name = rec.check_number
            if rec.journal_id:
                name = f"{rec.journal_id.name} / {rec.check_number}"
            result.append((rec.id, name))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        domain = [('is_used', '=', False)]

        if self.env.context.get('default_journal_id'):
            domain.append(('journal_id', '=', self.env.context['default_journal_id']))

        if name:
            domain.append(('check_number', operator, name))

        domain += args
        records = self.search(domain, limit=limit)
        return records.name_get()


