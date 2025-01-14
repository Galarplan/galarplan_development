# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
from odoo.exceptions import ValidationError,UserError
from odoo import api, fields, models, _


class ResPartnerBank(models.Model):
    _inherit="res.partner.bank"

    tercero = fields.Boolean("Tercero",default=False)
    identificacion_tercero = fields.Char("# Identificacion Tercero")
    nombre_tercero = fields.Char("Nombre de Cuenta Tercero")
    l10n_latam_identification_tercero_id = fields.Many2one("l10n_latam.identification.type",
                                                           "Tipo de Identificacion Tercero")
