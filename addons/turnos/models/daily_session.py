# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
from odoo.exceptions import UserError

class DailySession(models.Model):
    _name = 'daily.session'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Sesion Diaria'

    @api.model
    def default_get(self, fields_list):
        result = super().default_get(fields_list)
        turn_establishment = self.env['turn.establishment.module'].search([('active', '=', True)])
        turn_establishment2 = self.env['daily.session.module'].search(
            [('daily_session_id.state', '!=', 'ended')]).mapped(
            'turn_establishment_module_id')
        set_lista2 = set(turn_establishment2.ids)
        lista_on = [x for x in turn_establishment.ids if x not in set_lista2]
        all_lines = []
        for line in self.env['turn.establishment.module'].browse(lista_on):
            all_lines.append((0, 0, {'turn_establishment_module_id': line.id,
                                     'location':line.location,
                                     }))
        result['module_ids'] = all_lines
        return result

    @api.model
    def _get_default_turn_establishment_id(self):
        srch=self.env["turn.establishment"].sudo().search([('company_id','=',self.env.company.id),('active','=',True)])
        return srch and srch.id or False

    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        index=True,
        default=lambda self: self.env.company, tracking=True
    )
    turn_establishment_id = fields.Many2one('turn.establishment', string='Establecimiento', required=True,tracking=True,default=_get_default_turn_establishment_id)
    date = fields.Date(string='Fecha', required=True, default=fields.Date.context_today,tracking=True)
    date_start = fields.Datetime(string='Inicio', required=False,tracking=True)
    date_end = fields.Datetime(string='Fin', required=False,tracking=True)
    state = fields.Selection([
        ('draft', 'Preliminar'),
        ('started', 'Iniciado'),
        ('ended', 'Finalizado')
    ], default='draft', string='Estado',tracking=True)
    module_ids=fields.One2many("daily.session.module", "daily_session_id", "Modulos")

    ticket_ids = fields.One2many('turn.ticket', 'daily_session_id', 'Tickets')
    counter_tickets = fields.Integer(compute='_get_compute_counters', store=True, readonly=True)

    counter_draft = fields.Integer("Preliminares", compute="_get_compute_counters", store=True, readonly=True)
    counter_started = fields.Integer("Iniciados", compute="_get_compute_counters", store=True, readonly=True)
    counter_ended = fields.Integer("Finalizados", compute="_get_compute_counters", store=True, readonly=True)
    counter_cancelled = fields.Integer("Anulados", compute="_get_compute_counters", store=True, readonly=True)

    @api.depends('ticket_ids', 'ticket_ids.state')
    def _get_compute_counters(self):
        for brw_each in self:
            line = brw_each.ticket_ids
            brw_each.counter_tickets=len(line)
            brw_each.counter_draft = len(line.filtered(lambda x: x.state == 'draft'))
            brw_each.counter_started = len(line.filtered(lambda x: x.state == 'started'))
            brw_each.counter_ended = len(line.filtered(lambda x: x.state == 'ended'))
            brw_each.counter_cancelled = len(line.filtered(lambda x: x.state == 'cancelled'))


    @api.onchange('company_id')
    def onchange_company_id(self):
        self.turn_establishment_id = False

    _check_company_auto = True

    _rec_name="id"
    _order="id desc"

    @api.onchange('turn_establishment_id')
    def onchange_turn_establishment_id(self):
        if self.turn_establishment_id:
            all_lines = [(5,)]
            for line in self.turn_establishment_id.module_ids:
                all_lines.append((0, 0, {'turn_establishment_module_id': line.id,
                                         'location': line.location,
                                         'sequence':line.sequence
                                         }))
            self.module_ids= all_lines
            return
        self.module_ids=[(5,)]

    def unlink(self):
        for brw_each in self:
            if brw_each.state != 'draft':
                raise UserError(_('No puede eliminar sesiones que no esten en borrador'))
        return super(DailySession, self).unlink()

    def action_draft(self):
        for brw_each in self:
            brw_each.write({"state":"draft"})
        return True

    def action_started(self):
        for brw_each in self:
            brw_each.validate_start_sessions()
            brw_each.write({"state":"started",
                            "date_start":fields.Datetime.now()})
        return True

    def action_ended(self):
        for brw_each in self:
            brw_each.validate_ended_sessions()
            brw_each.write({"state":"ended","date_end":fields.Datetime.now() })
        return True

    def validate_start_sessions(self):
        pass

    def validate_ended_sessions(self):
        pass

    @api.constrains('date', 'turn_establishment_id', 'state')
    def _check_unique_active_session(self):
        for record in self:
            if record.state in ('draft', 'started'):
                existing_sessions = self.search([
                    ('date', '=', record.date),
                    ('turn_establishment_id', '=', record.turn_establishment_id.id),
                    ('state', 'in', ('draft', 'started')),
                    ('id', '!=', record.id)
                ])
                if existing_sessions:
                    raise models.ValidationError(
                            "Solo se permite una sesión activa (borrador o iniciada) por día y por establecimiento.")

    def action_call_ticket(self):
        self.ensure_one()
        action =self.env.ref('turnos.action_turn_ticket').sudo()  # Reemplaza 'module_name' por el nombre de tu módulo
        return {
            'type': 'ir.actions.act_window',
            'name': action.name,
            'res_model': action.res_model,
            'view_mode': action.view_mode,
            'views': [[False, 'tree'],[False, 'form']],
            'view_id': action.view_id.id,
            'context': action.context,
            'domain': f"[('id', 'in', {self.ticket_ids.ids})]",
            'search_view_id': action.search_view_id.id,
        }

