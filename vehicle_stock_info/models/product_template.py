from odoo import models, fields, api
from odoo.exceptions import ValidationError

VEHICLE_STATUS = [('new', 'Nuevo'), ('used', 'Usado')]

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_a_vehicle = fields.Boolean(string="Is a Vehicle")
    chassis_number = fields.Char(string="Chassis Number", unique=True, index=True)
    vehicle_status = fields.Selection(VEHICLE_STATUS, string="Vehicle Status")
    vehicle_color = fields.Char(string="Vehicle Color")

    @api.constrains('chassis_number')
    def _check_chassis_unique(self):
        for record in self:
            if record.chassis_number and self.search_count([('chassis_number', '=', record.chassis_number)]) > 1:
                raise ValidationError("The chassis number must be unique.")
