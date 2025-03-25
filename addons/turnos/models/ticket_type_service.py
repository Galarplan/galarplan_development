# -*- coding: utf-8 -*-
from odoo import models, fields, api


class TicketTypeService(models.Model):
    _name = 'ticket.type.service'
    _description = 'Tipo de Servicio'

    name = fields.Char("Nombre", required=True)
    service_ids = fields.One2many('ticket.service', 'type_id', "Servicios")
    active = fields.Boolean("Activo", default=True, tracking=True)

    _order = "name asc"
