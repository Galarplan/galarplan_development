from odoo import models, fields, api

class AttentionDevolution(models.Model):
    _name = 'attention.devolution'
    _description = 'Devolutions Management'
    _order = 'date desc'

    client_id = fields.Many2one('res.partner', string='Cliente', required=True)
    plan_type = fields.Char(string='Tipo')
    plan_start_date = fields.Date(string='Fecha Ingreso Plan')
    return_request_date = fields.Date(string='Fecha Requerimiento Devolucion')
    paid_value = fields.Float(string='Valor Pagado')
    return_date = fields.Date(string='Fecha Devolucion')
    liquidated_value = fields.Float(string='Valor Liquidado')
    check_status = fields.Selection([
        ('pending', 'Pendiente'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado')
    ], string='Status Cheque')
    payment_status = fields.Selection([
        ('pending', 'Pendiente'),
        ('paid', 'Pagado'),
        ('cancelled', 'Cancelado')
    ], string='Status Pago')