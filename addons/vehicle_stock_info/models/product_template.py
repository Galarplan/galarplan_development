from odoo import models, fields, api
from odoo.exceptions import ValidationError

VEHICLE_STATUS = [('nuevo', 'Nuevo'), ('usado', 'Usado')]



class VehicleBrand(models.Model):
    _name = 'vehicle.brand'
    _description = 'Marca de Vehículo'

    name = fields.Char(string="Marca", required=True)
    description = fields.Text(string="Descripción")

    _sql_constraints = [
        ('unique_brand_name', 'unique(name)', "El nombre de la marca debe ser único."),
    ]


class VehicleModel(models.Model):
    _name = 'vehicle.model'
    _description = 'Modelo de Vehículo'

    name = fields.Char(string="Modelo", required=True)
    brand_id = fields.Many2one('vehicle.brand', string="Marca", required=True)
    description = fields.Text(string="Descripción")

    _sql_constraints = [
        ('unique_model_name', 'unique(name, brand_id)', "El modelo debe ser único por marca."),
    ]


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Campos para Vehículo
    is_a_vehicle = fields.Boolean(string="¿Es un Vehículo?")
    chassis_number = fields.Char(string="Número de Chasis", unique=True, index=True)
    vehicle_status = fields.Selection(VEHICLE_STATUS, string="Estado del Vehículo")
    vehicle_color = fields.Char(string="Color del Vehículo")
    km_value = fields.Float(string='Km', default = 0)
    registration_date = fields.Date(string="Fecha de Registro")

    # Campos para Modelo
    number_of_seats = fields.Integer(string="Número de Asientos")
    number_of_doors = fields.Integer(string="Número de Puertas")
    number_of_tires = fields.Integer(string="Número de Llantas")
    number_of_axles = fields.Integer(string="Número de Ejes")
    model_year = fields.Char(string="Año del Modelo")

    # Campos para Motor
    engine_number = fields.Char(string="Número de Motor")
    ramw_number = fields.Char(string="Número RAMW")
    transmission = fields.Char(string="Transmisión")
    fuel_type = fields.Char(string="Tipo de Combustible")
    cylinder_capacity = fields.Float(string="Capacidad de Cilindrada")
    co2_emissions = fields.Float(string="Emisiones de CO2")
    horsepower = fields.Float(string="Caballos de Fuerza")
    power_kw = fields.Float(string="Potencia (kW)")

    vehicle_brand_id = fields.Many2one('vehicle.brand', string="Marca del Vehículo")
    vehicle_model_id = fields.Many2one('vehicle.model', string="Modelo del Vehículo")
    vehicle_type = fields.Many2one('vehicle.type',string='Tipo de vehiculo')
    vehicle_model_domain_ids = fields.Many2many(
        'vehicle.model', compute='_compute_vehicle_model_domain', store=False, string="Domain for Vehicle Models"
    )

    @api.depends('vehicle_brand_id')
    def _compute_vehicle_model_domain(self):
        """Actualizar los modelos disponibles según la marca seleccionada."""
        for record in self:
            if record.vehicle_brand_id:
                record.vehicle_model_domain_ids = self.env['vehicle.model'].search([('brand_id', '=', record.vehicle_brand_id.id)])
            else:
                record.vehicle_model_domain_ids = self.env['vehicle.model'].search([])

    @api.constrains('chassis_number')
    def _check_chassis_unique(self):
        for record in self:
            if record.chassis_number and self.search_count([('chassis_number', '=', record.chassis_number)]) > 1:
                raise ValidationError("El número de chasis debe ser único.")
            
    @api.model
    def create(self, vals):
        """Sobrescribir el método create para asignar el número de chasis como referencia interna."""
        # Verificar si es un vehículo y si tiene número de chasis
        if vals.get('is_a_vehicle') and vals.get('chassis_number'):
            vals['default_code'] = vals.get('chassis_number')
        return super(ProductTemplate, self).create(vals)

