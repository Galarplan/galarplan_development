# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
from odoo.exceptions import ValidationError,UserError
from odoo import api, fields, models, _


class ResPartnerBank(models.Model):
    _inherit="res.partner.bank"

    tipo_cuenta = fields.Selection([('Corriente', 'Corriente'),
                                         ('Ahorro', 'Ahorro'),
                                         # ('Tarjeta', 'Tarjeta'),
                                         # ('Virtual', 'Virtual')
                                         ], string="Tipo de Cuenta")