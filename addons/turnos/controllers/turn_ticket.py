from odoo import http
from odoo.http import request
import json
from odoo import fields


class TurnTicketController(http.Controller):

    @http.route('/api/create_ticket', type='json', auth='user', methods=['POST'], csrf=False)
    def create_ticket(self, **kwargs):
        data = request.get_json_data()#parametros
        print(data)
        required_fields = ['turn_establishment_id',
                           'ticket_service_id',
                           'car_plate',
                           'partner_id', 'html_detail','location']
        print(data)
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return {'error': 'Missing required fields', 'missing_fields': missing_fields}
        try:
            OBJ_TICKET=request.env['turn.ticket']
            brw_establishment=request.env["turn.establishment"].browse(data['turn_establishment_id'])
            vals={
                'turn_establishment_id': brw_establishment.id,
                'ticket_service_id': data['ticket_service_id'],
                'car_plate': data['car_plate'],
                'partner_id': data['partner_id'],
                'html_detail': data['html_detail'],
                'location': data['location'],
            }
            result=OBJ_TICKET.assign_automatic_user( brw_establishment.company_id.id,
                                               data['ticket_service_id'],
                                               brw_establishment.id,
                                               data['location'],
                                               date=fields.Date.context_today(OBJ_TICKET))
            if not result:
                return {'error':'No hay turnos configurados para el establecimiento y tipo de servicio'}
            result=result[0]
            vals["daily_session_module_id"]=result["daily_session_module_id"]
            vals["user_id"]=result["user_id"]
            ticket = OBJ_TICKET.create(vals)
            return {'success': True,
                    'ticket_id': ticket.id}
        except Exception as e:
            return {'error': str(e)}
