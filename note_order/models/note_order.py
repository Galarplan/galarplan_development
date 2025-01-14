from odoo import fields, models

class NoteOrder(models.Model):
    _name = 'note.order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Nota de Pedido'

    name = fields.Char(string="Número de Nota", required=True, copy=False, readonly=True, default=lambda self: 'New')
    customer_name = fields.Char(string="Cliente")
    customer_address = fields.Char(string="Dirección")
    customer_phone = fields.Char(string="Teléfono")
    vehicle_brand = fields.Char(string="Marca del Vehículo")
    vehicle_model = fields.Char(string="Modelo")
    vehicle_version = fields.Char(string="Versión")
    vehicle_chassis = fields.Char(string="Chasis")
    vehicle_engine = fields.Char(string="Motor")
    vehicle_color = fields.Char(string="Color")
    vehicle_year = fields.Integer(string="Año")
    vehicle_plate = fields.Char(string="Placa")
    total_price = fields.Monetary(string="Precio Total", currency_field='currency_id')
    amount_financed = fields.Monetary(string="Saldo a Financiar", currency_field='currency_id')
    amount_downpayment = fields.Monetary(string="Contraentrega", currency_field='currency_id')
    comments = fields.Text(string="Comentarios y Observaciones")
    accessories = fields.Text(string="Accesorios")
    currency_id = fields.Many2one('res.currency', string='Moneda', default=lambda self: self.env.company.currency_id)
    salesperson = fields.Many2one('res.users', string="Vendedor")
    approval_manager = fields.Many2one('res.users', string="Autorizado por Gerencia")
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado'),
        ('invoiced', 'Facturado')
    ], string="Estado", default='draft')

    def action_confirm(self):
        self.state = 'confirmed'

    def action_invoice(self):
        self.state = 'invoiced'
