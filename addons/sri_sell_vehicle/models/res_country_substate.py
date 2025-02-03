# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResCountrySubstate(models.Model):
    _name = 'res.country.substate'
    _description = 'cantones para provincias'

    name = fields.Char(string='Nombre del canton')
    code = fields.Char(string='Codigo del Canton')
    country_state = fields.Many2one('res.country.state',string='Provincia')

    
    