from odoo import _, api, fields, models


class InvocieHistory(models.Model):
    _name = 'invoice.history'
    _description = 'Historico de facturas'

    name = fields.Char('Nombre del cliente')
    invoice_date = fields.Date('Fecha de Factura')
    invoice_due_date = fields.Date('Fecha de Vencimiento')
    reference = fields.Char('Referencia')
    document_number = fields.Char('Numero de documento')
    total_invoice = fields.Float('Total de la factura')
    total_forpayment = fields.Float('Importe Adeudado')
    payment_history = fields.Text('Historico de pagos')
    tipo = fields.Selection([('cliente','Factura Cliente'),('proveedor','Factura Proveedor')])