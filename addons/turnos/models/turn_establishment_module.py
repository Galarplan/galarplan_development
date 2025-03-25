# -*- coding: utf-8 -*-
from odoo import models, fields, api

class TurnEstablishmentModule(models.Model):
    _name = 'turn.establishment.module'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Modulo del Establecimiento'

    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        index=True,
        default=lambda self: self.env.company, tracking=True
    )
    turn_establishment_id=fields.Many2one("turn.establishment","Establecimiento",ondelete="cascade",tracking=True)
    name = fields.Char(string='Nombre', required=True,tracking=True)
    active=fields.Boolean("Activo",default=True,tracking=True)
    location=fields.Selection([('location_1', 'Rtv1'),
                                 ('location_2', 'Rtv2'),
                                ('*', 'Todos')
                           ],string="Linea",required=False,default=None)
    sequence=fields.Integer("Secuencia",required=True,default=1)

    @api.onchange('company_id')
    def onchange_company_id(self):
        self.turn_establishment_id=False

    _check_company_auto = True

    _order="turn_establishment_id asc,sequence asc"