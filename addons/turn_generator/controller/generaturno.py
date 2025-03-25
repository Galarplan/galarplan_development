from odoo import http
from odoo.http import request

class GeneradorTurnosController(http.Controller):
    @http.route('/generar_turno', type='json', auth='public')
    def generar_turno(self, placa):
        print('metoo=======')
        vehiculo = request.env['generador_turnos.vehiculo'].sudo().search([('placa', '=', placa)], limit=1)
        if not vehiculo:
            vehiculo = request.env['generador_turnos.vehiculo'].sudo().create({'placa': placa})
        turno = request.env['generador_turnos.turno'].sudo().create({'vehiculo_id': vehiculo.id})
        return {'numero_turno': turno.numero_turno}