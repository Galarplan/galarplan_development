# -*- coding: utf-8 -*-
from odoo import models, fields, api

class TicketService(models.Model):
    _name = 'ticket.service'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Servicios'

    code=fields.Char("Código",required=True,tracking=True)
    name=fields.Char("Nombre",required=True,tracking=True)
    type_id=fields.Many2one('ticket.type.service',"Tipo",on_delete="cascade",tracking=True)
    active = fields.Boolean("Activo", default=True,tracking=True)

    _order="name asc"