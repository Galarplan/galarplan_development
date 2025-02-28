from odoo import _, api, fields, models

class AccountMove(models.Model):
    _inherit = "account.move"


    details_ids = fields.One2many('custom.detail.line','move_id',string='Detalle')
    parcial = fields.Boolean(string="Factura Parcial")
    datos_pagos_json = fields.Text(string="Pagos Json")



class PaymentDetails(models.Model):
    _name = 'custom.detail.line'

    move_id = fields.Many2one('account.move', ondelete='cascade')
    name = fields.Char(string='Descripción', required=True)
    amount = fields.Float(string="Monto")