from odoo import models, fields

class Turno(models.Model):
    _name = 'generador_turnos.turno'
    _description = 'Turno'

    vehiculo_id = fields.Many2one('generador_turnos.vehiculo', string='Vehículo', required=True)
    numero_turno = fields.Char(string='Número de Turno', required=True, default=lambda self: self._generar_turno())
    fecha_creacion = fields.Datetime(string='Fecha de Creación', default=fields.Datetime.now)

    def _generar_turno(self):
        # Genera un número de turno único (puedes personalizar esta lógica)
        return self.env['ir.sequence'].next_by_code('generador_turnos.turno.sequence')