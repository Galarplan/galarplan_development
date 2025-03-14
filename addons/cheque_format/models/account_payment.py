from odoo import _, api, fields, models
from num2words import num2words

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    bank_cheque_id = fields.Many2one('cheque.printing', string='Formato del cheque')

    beneficiario_id = fields.Many2one('res.partner',string='Beneficiario')

    nombre_cheque = fields.Char(string="Nombre Corto")

    def convertir_monto_a_palabras(self, monto):
        # Ensure monto is a string
        monto_str = "{:.2f}".format(monto)
        
        # Replace a period (.) with a comma (,) if present
        monto_str = monto_str.replace('.', ',')
        print('=======================',monto_str)
        
        # Split the monto into integer and decimal parts
        if ',' in monto_str:
            parte_entera, parte_decimal = monto_str.split(',')
        else:
            parte_entera = monto_str
            parte_decimal = '00'  # Default to '00' if no decimal part exists
        
        print('====================',parte_entera,parte_decimal)

        # Convert the integer part to words
        palabras_enteras = num2words(int(parte_entera), lang='es')
        
        palabras_enteras = palabras_enteras.upper()
        # Format the decimal part
        if parte_decimal == '0':
            parte_decimal = '00'
        
        palabras_decimales = f"CON {parte_decimal}/100"
        
        # Combine both parts
        resultado = f"{palabras_enteras} {palabras_decimales}"
        
        return resultado