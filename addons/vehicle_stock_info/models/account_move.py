# -*- coding: utf-8 -*-

from odoo import models, fields, api

MONTHS = {
    1: 'ENERO',
    2: 'FEBRERO',
    3: 'MARZO',
    4: 'ABRIL',
    5: 'MAYO',
    6: 'JUNIO',
    7: 'JULIO',
    8: 'AGOSTO',
    9: 'SEPTIEMBRE',
    10: 'OCTUBRE',
    11: 'NOVIEMBRE',
    12: 'DICIEMBRE',
}


class AccountMove(models.Model):
    _inherit = 'account.move'

    invoice_user_id_com = fields.Many2one('hr.employee',string='Comercial')
    details_invoice_line_id = fields.One2many('account.details.line', 'move_id', string='Detalles')




    def _l10n_ec_get_invoice_additional_info(self):
    # Diccionario base con la referencia de la factura
        additional_info = {
            "Referencia": self.name,  # Reference
        }

        # Agregar detalles de las líneas adicionales
        for index, line in enumerate(self.details_invoice_line_id, start=1):
            additional_info[f"{line.campo}"] = line.descripcion

        return additional_info
    


class AccountDetailLine(models.Model):
    _name = 'account.details.line'

    move_id = fields.Many2one('account.move',string='movimiento')
    campo = fields.Char(string='Detalle')
    descripcion = fields.Char(string='Descripcion')



