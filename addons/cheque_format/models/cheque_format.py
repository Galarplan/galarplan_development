from odoo import models, fields


FLOAT_FIELDS = [('right','Derecha'),('left','Izquierda'),('center','Centro')]

class ChequePrinting(models.Model):
    _name = 'cheque.printing'
    _description = 'Cheque Printing Configuration'

    # Campos básicos
    name = fields.Char(string='Cheque Format', required=True, placeholder="Cheque Format")
    active = fields.Boolean(string='Active', default=True)
    type_letter = fields.Char(string='Tipo de Letra')
    company_id = fields.Many2one('res.company', string='Company', required=True)
    bank_id = fields.Many2one('res.bank', string='Bank')
    cheque_height = fields.Float(string='Cheque Height')
    cheque_width = fields.Float(string='Cheque Width')

    # Configuración general
    currency_symbol = fields.Char(string='Currency Symbol')
    fd_use_city = fields.Boolean(string='Use City in First Date')
    sc_use_second_date = fields.Boolean(string='Use Second Date')
    sb_use_signature = fields.Boolean(string='Use Signature Box')

    # Beneficiary (Beneficiario)
    bf_top_margin = fields.Float(string='Top Margin')
    bf_left_margin = fields.Float(string='Left Margin')
    bf_width = fields.Float(string='Width')
    bf_font_size = fields.Float(string='Font Size')
    bf_float = fields.Selection(FLOAT_FIELDS,string='Float')
    bf_char_spacing = fields.Float(string='Character Spacing')

    # Amount Value (Valor del Monto)
    af_top_margin = fields.Float(string='Top Margin')
    af_left_margin = fields.Float(string='Left Margin')
    af_width = fields.Float(string='Width')
    af_font_size = fields.Float(string='Font Size')
    af_float = fields.Selection(FLOAT_FIELDS,string='Float')

    # Amount in Word (Monto en Letras)
    fl_top_margin = fields.Float(string='Top Margin')
    fl_left_margin = fields.Float(string='Left Margin')
    fl_width = fields.Float(string='Width')
    fl_font_size = fields.Float(string='Font Size')
    fl_float = fields.Selection(FLOAT_FIELDS,string='Float')
    fl_height = fields.Float(string='Height')

    # First Date (Primera Fecha)
    fd_top_margin = fields.Float(string='Top Margin')
    fd_left_margin = fields.Float(string='Left Margin')
    fd_width = fields.Float(string='Width')
    fd_city_position = fields.Char(string='City Position', help="Position of the city in the first date.")
    fd_font_size = fields.Float(string='Font Size')
    fd_float = fields.Selection(FLOAT_FIELDS,string='Float')
    fd_date_format = fields.Char(string='Date Format', required=True)

    # Second Date (Segunda Fecha)
    sc_top_margin = fields.Float(string='Top Margin')
    sc_left_margin = fields.Float(string='Left Margin')
    sc_width = fields.Float(string='Width')
    sc_use_second_city = fields.Boolean(string='Use City in Second Date')
    sc_font_size = fields.Float(string='Font Size')
    sc_float = fields.Selection(FLOAT_FIELDS,string='Float')
    sc_date_format = fields.Char(string='Date Format')
    sc_city_position = fields.Char(string='City Position', help="Position of the city in the second date.")

    # Signature Box (Caja de Firma)
    sb_top_margin = fields.Float(string='Top Margin')
    sb_left_margin = fields.Float(string='Left Margin')
    sb_width = fields.Float(string='Width')
    sb_float = fields.Selection(FLOAT_FIELDS,string='Float')
    sb_height = fields.Float(string='Height')