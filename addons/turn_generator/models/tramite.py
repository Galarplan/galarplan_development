from odoo import _, api, fields, models

class Tramite(models.Model):
    _name = 'tramite.root'
    _descripcion = 'Tramite Principal'

    opcion_id = fields.Many2one('generador_turnos.opcion','Opcion')
    service_name = fields.Char('Nombre del Servicio')
    asociated_service = fields.Many2one('ticket.service',string='Servicio Asociado')
    have_services = fields.Boolean('Tiene Servicios?',default=False)
    have_requeriments = fields.Boolean('Tiene Requisitos?',default = False)
    have_payments = fields.Boolean('Tiene Ordenes Pago?', default = False)
    tramite_lines = fields.One2many('tramite.service.line','tramite_id','Servicios')
    tramite_requeriment_lines = fields.One2many('tramite.requeriments.line','tramite_id','Requisitos')
    tramite_produt_lines = fields.One2many('tramite.products','tramite_id','Orden de Pago')
    

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, record.service_name))
        return result




class TramiteServices(models.Model):
    _name = 'tramite.service.line'
    _descripcion = 'Lineas del tramite'

    tramite_id = fields.Many2one('tramite.root')

    name = fields.Char('Nombre')



class TramiteServices(models.Model):
    _name = 'tramite.requeriments.line'
    _descripcion = 'Lineas de requeriminetos'

    tramite_id = fields.Many2one('tramite.root')

    name = fields.Char('Nombre')


class TramiteProduct(models.Model):
    _name = 'tramite.products'

    tramite_id = fields.Many2one('tramite.root')
    product_id = fields.Many2one('product.product','producto')
    costo = fields.Float(string='Costo', compute='_compute_costo', store=True)

    @api.depends('product_id')
    def _compute_costo(self):
        for record in self:
            record.costo = record.product_id.list_price if record.product_id else 0.0

