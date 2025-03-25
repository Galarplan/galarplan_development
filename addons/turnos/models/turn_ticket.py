# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError


class TurnTicket(models.Model):
    _name = 'turn.ticket'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Turnos'

    sequence = fields.Char(string='Secuencia')
    service_selected = fields.Char(string="Servicio Seleccionado Kiosko")
    company_id = fields.Many2one(related="turn_establishment_id.company_id", store=True, readonly=True)
    turn_establishment_id = fields.Many2one('turn.establishment', string='Establecimiento', required=True,
                                            tracking=True)
    daily_session_id=fields.Many2one(related="daily_session_module_id.daily_session_id",store=True,readonly=True)
    daily_session_module_id = fields.Many2one('daily.session.module', 'Sesion Diaria por Modulo', tracking=True)
    ticket_service_id=fields.Many2one('ticket.service','Servicio',required=True, tracking=True)
    car_plate=fields.Char("# de Placa",required=True, tracking=True)
    partner_id=fields.Many2one("res.partner","Cliente", tracking=True)
    user_id=fields.Many2one('res.users','Usuario',required=True, tracking=True)
    date=fields.Date(string="Fecha",required=True,default=fields.Date.context_today, tracking=True)
    date_start = fields.Datetime(string='Inicio', required=False, tracking=True)
    date_end = fields.Datetime(string='Fin', required=False, tracking=True)
    state = fields.Selection([
        ('draft', 'Preliminar'),
        ('started', 'Iniciado'),
        ('ended', 'Finalizado'),
        ('cancelled', 'Anulado')
    ], default='draft', string='Estado', tracking=True)
    html_detail=fields.Html("Detalle", tracking=True)
    location = fields.Selection([('location_1', 'Rtv1'),
                                 ('location_2', 'Rtv2'),
                                 ('*','Todos'),
                                 ], string="Linea", required=False, default=None, tracking=True)

    call_count=fields.Integer(string='Contador de Llamadas', default=0,
                              help='Cantidad de veces que se ha pulsado el botón',tracking=True)

    computed_date = fields.Datetime(string="Fecha Calculada", compute="_compute_computed_date", store=False)

    



    @api.depends('state', 'date_end')
    def _compute_computed_date(self):
        for record in self:
            if record.state in ['draft', 'started']:
                record.computed_date = fields.Datetime.now()
            else:
                record.computed_date = record.date_end

    def action_call(self):
        for record in self:
            record.call_count += 1

    _check_company_auto = True
    _rec_name="id"

    def unlink(self):
        raise UserError(_('Los turnos no pueden ser eliminados en caso de que no se necesite puede proceder a anularlo'))

    def action_draft(self):
        for brw_each in self:
            brw_each.write({"state": "draft"})
        return True

    def action_started(self):
        for brw_each in self:
            brw_each.action_validation()
            brw_each.write({"state": "started", "date_start": fields.Datetime.now()})
        return True

    def action_ended(self):
        for brw_each in self:
            brw_each.write({"state": "ended", "date_end": fields.Datetime.now()})
        return True

    def action_cancelled(self):
        for brw_each in self:
            brw_each.write({"state": "cancelled", "date_end": fields.Datetime.now()})
        return True

    def action_validation(self):
        def number_list(numero, lista):
            return all(numero <= x for x in lista)

        turns = self.search([('user_id', '=', self.user_id.id), ('state', 'in', ('draft', 'started'))]).mapped('id')
        if not number_list(self.id, turns):
            raise ValidationError(_('Se encontraron turnos anteriores'))
        return True

    @api.onchange('ticket_service_id', 'company_id', 'turn_establishment_id','location')
    def onchange_turn(self):
        if self.ticket_service_id and self.company_id and self.turn_establishment_id and self.location:
            result=self.assign_automatic_user(self.company_id.id,self.ticket_service_id.id,self.turn_establishment_id.id,self.location)
            if not result:
                raise ValidationError(_('No hay turnos configurados para el establecimiento y tipo de servicio'))
            result=result[0]
            self.daily_session_module_id=result["daily_session_module_id"]
            self.user_id=result["user_id"]
            return
        self.daily_session_module_id=False
        self.user_id=False


    @api.model
    def assign_automatic_user(self,company_id, ticket_service_id, establishment_id,location, date=None):
        if date is None:
            date = fields.Date.context_today(self)
        self._cr.execute(''';with variables as (
    	select %s::int as company_id,
    		%s::int as establishment_id,
    		%s::date as date,
    		%s::int as service_id ,
    		%s::varchar(10) as location 
    ) , services_maps as (
    	 SELECT ts.id, ts.name, s.id AS service_id, s.name AS service_name
        FROM ticket_type_service ts
        JOIN ticket_service s ON s.type_id = ts.id
    	inner join variables on s.id=variables.service_id
        WHERE ts.active = True
    )

    select te.id as turn_establishment_id,
    	tem.id as turn_establishment_module_id,
    	tem.name,
    	ds.id,ds.date ,
    	dsm.counter_tickets,
    	dsm.id as daily_session_module_id,
    	dsm.user_id 
    from 
    variables 
    inner join turn_establishment te on te.company_id=variables.company_id and te.id=variables.establishment_id
    inner join turn_establishment_module tem on tem.turn_establishment_id= te.id
    inner join daily_session ds on ds.turn_establishment_id=te.id 
    inner join daily_session_module dsm on dsm.daily_session_id=ds.id
    	and dsm.turn_establishment_module_id=tem.id and ds.date=variables.date and ds.state='started'
    inner join daily_session_ticket_type_service rlstt on
    	rlstt.daily_session_module_id=dsm.id
    inner join services_maps sm on sm.id=rlstt.ticket_type_service_id	
    where te.active and tem.active and 
		(dsm.location='*' or dsm.location=variables.location) 
    order by dsm.counter_tickets asc,tem.sequence asc 
     ''',(company_id, establishment_id,  date,ticket_service_id,location))
        result=self._cr.dictfetchall()
        return result
    


    @api.model
    def create_ticket_from_xmlrpc(self, data):
        """
        Función para crear un ticket a partir de datos recibidos por XML-RPC.
        :param data: Diccionario con los datos necesarios para crear el ticket.
        :return: El ID del ticket creado.
        """
        establishment = self.env['turn.establishment'].search([('name','=',data['turn_establishment_id'])],limit=1)
        if not establishment:
            raise ValidationError("El establecimiento no existe.")
        
        pre_service = self.env['tramite.root'].search([('service_name','=',data['ticket_service_id'])],limit=1)

        # service = self.env['ticket.service'].search([('name','=',)],limit=1)
        # if not service:
        #     raise ValidationError("El servicio no existe.")
        


        # partner = self.env['res.partner'].search([('name', '=', data['partner_id'])], limit=1)
        # if not partner:
        #     # Si no existe el partner, puedes crearlo automáticamente
        #     partner = self.env['res.partner'].create({
        #         'name': data['partner_id'],
        #         'email': data.get('correo', ''),
        #     })

        result = self.assign_automatic_user(establishment.company_id.id,
                                            pre_service.asociated_service.id,
                                            establishment.id,
                                            data['location'],
                                            date=fields.Date.context_today(self))
        if not result:
                return {'error':'No hay turnos configurados para el establecimiento y tipo de servicio'}
        result=result[0]
        
        
        # Crear el ticket
        ticket_data = {
            'turn_establishment_id': establishment.id,
            'ticket_service_id': pre_service.asociated_service.id,
            'car_plate': data['car_plate'],
            'sequence' : self.env['ir.sequence'].next_by_code('turn_assign'),
            'service_selected': data['ticket_service_id'],
            'daily_session_module_id':result["daily_session_module_id"],
            # 'partner_id': partner.id,
            'user_id': result["user_id"],  # Usuario actual
            'date': fields.Date.context_today(self),
            'html_detail': data['html_detail'],
            'location': data['location'],
            
            # Agrega más campos según sea necesario
        }
        ticket = self.create(ticket_data)

        return {'ticket_id': ticket.id,
                'sequence': ticket.sequence,
                'placa': ticket.car_plate,
                'tramite': ticket.service_selected}