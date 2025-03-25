# -*- coding: utf-8 -*-
from odoo import models, fields, api

class TurnEstablishment(models.Model):
    _name = 'turn.establishment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Establecimiento'

    name = fields.Char(string='Nombre', required=True,tracking=True)
    company_id = fields.Many2one(
        'res.company', 
        string='Compañía',
        required=True, 
        index=True, 
        default=lambda self: self.env.company,tracking=True
    )
    active=fields.Boolean("Activo",default=True,tracking=True)
    module_ids = fields.One2many("turn.establishment.module", "turn_establishment_id", "Modulos")

    _check_company_auto = True