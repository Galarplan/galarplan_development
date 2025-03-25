# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
from odoo.exceptions import UserError


class DailySessionModule(models.Model):
    _name = 'daily.session.module'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Sesion Diaria por Modulo'

    company_id = fields.Many2one(related="daily_session_id.company_id", store=True, readonly=True)
    daily_session_id = fields.Many2one('daily.session', 'Sesion Diaria', on_delete="cascade")
    user_id = fields.Many2one("res.users", "Usuario", required=False)
    turn_establishment_module_id = fields.Many2one("turn.establishment.module", "Modulo", reuired=True)
    type_service_ids = fields.Many2many(
        "ticket.type.service", "daily_session_ticket_type_service",
        "daily_session_module_id", "ticket_type_service_id", string="Servicios",
        default=lambda self: self._default_type_service_ids()
    )
    state = fields.Selection([
        ('active', 'Activo'),
        ('pause', 'Pausa'),
        ('inactive', 'Inactivo')
    ], default='active', string='Estado')

    location = fields.Selection([('location_1', 'Rtv1'),
                                 ('location_2', 'Rtv2'),
                                 ('*', 'Todos')
                                 ], string="Linea", required=False, default=None)
    ticket_ids=fields.One2many('turn.ticket','daily_session_module_id','Tickets')
    sequence = fields.Integer("Secuencia", required=True, default=1)

    counter_draft=fields.Integer("Preliminares",compute="_get_compute_counters",store=True,readonly=True)
    counter_started = fields.Integer("Iniciados", compute="_get_compute_counters", store=True, readonly=True)
    counter_ended = fields.Integer("Finalizados", compute="_get_compute_counters", store=True, readonly=True)
    counter_cancelled= fields.Integer("Anulados", compute="_get_compute_counters", store=True, readonly=True)
    date=fields.Date(related='daily_session_id.date',store=True,readonly=True)

    @api.depends('ticket_ids','ticket_ids.state')
    def _get_compute_counters(self):
        for brw_each in self:
            line=brw_each.ticket_ids
            brw_each.counter_tickets = len(line)
            brw_each.counter_draft=len(line.filtered(lambda x: x.state=='draft'))
            brw_each.counter_started = len(line.filtered(lambda x: x.state == 'started'))
            brw_each.counter_ended = len(line.filtered(lambda x: x.state == 'ended'))
            brw_each.counter_cancelled = len(line.filtered(lambda x: x.state == 'cancelled'))


    @api.onchange('turn_establishment_module_id')
    def onchange_turn_establishment_module_id(self):
        if not self.turn_establishment_module_id:
            self.location=None
        else:
            self.location=self.turn_establishment_module_id.location

    @api.model
    def _default_type_service_ids(self):
        """ Obtiene todos los servicios activos por defecto. """
        return self.env['ticket.type.service'].search([]).ids  # ('active', '=', True)

    counter_tickets = fields.Integer(compute='_get_compute_counters', store=True, readonly=True)

    _check_company_auto = True
    _rec_name = "turn_establishment_module_id"
    _order = "daily_session_id asc,sequence asc"

    @api.constrains('turn_establishment_module_id', 'user_id')
    def _check_unique_active_session(self):
        for record in self:
            ###
            if record.user_id:
                if self.search_count([('user_id', '=', record.user_id.id),
                                      ('daily_session_id','=',record.daily_session_id.id)
                                      ]) > 1:
                    raise models.ValidationError(
                        "Solo se permite una sesión activa por usuario.")
            if record.turn_establishment_module_id:
                if self.search_count(
                        [('turn_establishment_module_id', '=', record.turn_establishment_module_id.id),
                                      ('daily_session_id','=',record.daily_session_id.id)]) > 1:
                    raise models.ValidationError(
                        "Solo se permite una sesión por establecimiento.")
            ######
            existing_sessions = self.search([
                ('user_id', '=', record.user_id.id),
                ('turn_establishment_module_id', '=', record.turn_establishment_module_id.id),
                ('daily_session_id.state', 'in', ('draft', 'started')),
                ('id', '!=', record.id)
            ])
            if existing_sessions:
                if existing_sessions:
                    raise models.ValidationError(
                        "Solo se permite una sesión activa (borrador o iniciada) por día y por establecimiento.")
            ###modules
            existing_sessions = self.search([
                ('turn_establishment_module_id', '=', record.turn_establishment_module_id.id),
                ('daily_session_id.state', 'in', ('draft', 'started')),
                ('id', '!=', record.id)
            ])
            if existing_sessions:
                if existing_sessions:
                    raise models.ValidationError(
                        "Solo se permite una sesión activa (borrador o iniciada) por día y por modulo.")


    @api.model
    def assign_automatic_user(self, ticket_service_id, establishment_id, date=None):
        if date is None:
            date = fields.Date.context_today(self)
        # servicio por atender,sucursal,fecha por defecto la de hoy
        return True

    def unlink(self):
        for brw_each in self:
            if brw_each.counter_tickets>0:
                raise UserError(_('No puedes borrar una configuracion de sesion diaria si tiene tickets'))
        return super(DailySessionModule, self).unlink()

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
