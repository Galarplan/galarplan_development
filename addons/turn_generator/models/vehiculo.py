from odoo import models, fields

class Vehiculo(models.Model):
    _name = 'generador_turnos.vehiculo'
    _description = 'Vehículo'

    placa = fields.Char(string='Placa', required=True, unique=True)
    nombre = fields.Char(string="Nombre")
    correo = fields.Char(string="Correo")
    identificacion = fields.Char(string="Identificacion")
    modelo = fields.Char(string='Modelo')
    marca = fields.Char(string="Marca")
    anio = fields.Char(string='Año')
    fecha_creacion = fields.Datetime(string='Fecha de Creación', default=fields.Datetime.now)