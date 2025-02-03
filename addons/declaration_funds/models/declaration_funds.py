from odoo import models, fields, api

class DeclarationFunds(models.Model):
    _name = 'declaration.funds'
    _description = 'Declaración de Licitud de Fondos'

    tipo = fields.Selection([
        ('natural', 'Persona Natural'),
        ('juridica', 'Persona Jurídica'),
    ], string="Tipo", required=True, default='natural')
    date = fields.Date(string="Fecha", required=True, default=fields.Date.context_today)
    client_name = fields.Char(string="Nombre del Cliente", required=True)
    client_identification = fields.Char(string="CI/Pasaporte/RUC", required=True)
    address = fields.Char(string="Dirección")
    city = fields.Char(string="Ciudad")
    phone = fields.Char(string="Teléfono")
    email = fields.Char(string="Correo Electrónico")
    principal_activity = fields.Text(string="Actividad Principal")
    transaction_value = fields.Float(string="Valor de la Transacción (USD)", required=True)
    transaction_type = fields.Char(string="Tipo de Transacción")
    cash = fields.Float(string="Efectivo (USD)")
    check = fields.Float(string="Cheque (USD)")
    credit_card = fields.Float(string="Tarjeta de Crédito (USD)")
    bank_transfer = fields.Float(string="Transferencia Bancaria (USD)")
    bank_name = fields.Char(string="Banco de la Transferencia")
    direct_financing = fields.Float(string="Financiamiento Directo (USD)")
    financial_institution = fields.Char(string="Institución Financiera")
    funds_origin = fields.Text(string="Origen de los Fondos")
    # Campos adicionales para persona jurídica
    legal_representative = fields.Char(string="Representante Legal")
    legal_representative_id = fields.Char(string="CI/Pasaporte/RUC del Representante Legal")
