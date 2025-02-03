# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResCountryState(models.Model):
    _inherit = 'res.country.state'
    _description = 'sri_sell_vehicle.sri_sell_vehicle'

    country_state_code = fields.Char(string='Codigo de venta')