# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResCountryParish(models.Model):
    _name = 'res.country.parish'
    _description = 'Parroquias por cantón'

    name = fields.Char(string='Nombre de la parroquia')
    code = fields.Char(string='Código de la parroquia')
    substate_id = fields.Many2one(
        'res.country.substate',
        string='Cantón'
    )