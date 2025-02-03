from odoo import fields, models


VEHICLE_STATE = [('new','Nuevo'),('used','Usado')]

class AccountMove(models.Model):
    _inherit = 'account.move'

    is_vehicle = fields.Boolean(string="Venta de Vehículo", default=False)
    vehicle_status = fields.Selection(VEHICLE_STATE,string='Estado del Vehiculo')
