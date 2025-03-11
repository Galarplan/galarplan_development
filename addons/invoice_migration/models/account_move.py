from odoo import _, api, fields, models
from odoo.exceptions import ValidationError,UserError
import json

class AccountMove(models.Model):
    _inherit = "account.move"


    details_ids = fields.One2many('custom.detail.line','move_id',string='Detalle')
    parcial = fields.Boolean(string="Factura Parcial")
    datos_pagos_json = fields.Text(string="Pagos Json")
    total_antes = fields.Float(string='Importe total sistema antiguo')
    total_pagado = fields.Boolean(string="Pagada")
    

    def agregar_pagos(self):
        for record in self:
            if record.datos_pagos_json:
                try:
                    datos_pagos = json.loads(record.datos_pagos_json)
                    for pago in datos_pagos.get('content', []):
                        ref = pago.get('ref', '')
                        amount = pago.get('amount', 0.0)
                        if ref and amount:
                            record.details_ids.create({
                                'move_id': record.id,
                                'name': ref,
                                'amount': amount,
                            })
                except json.JSONDecodeError:
                    raise UserError("El formato del JSON en 'Pagos Json' no es válido.")



class PaymentDetails(models.Model):
    _name = 'custom.detail.line'

    move_id = fields.Many2one('account.move', ondelete='cascade')
    name = fields.Char(string='Descripción', required=True)
    amount = fields.Float(string="Monto")