
from odoo import models, fields, api, _


SEX_TYPE = [('F','Female'),('M',"Male")]
INSTALLATION_TYPE = [('01','Own'),('02','Rent'),('03','Other')]

class EnterpriseCreditRequest(models.Model):
    _name = 'enterprise.request'
    _description = 'customer credit request'
    _inherit = 'credit.request.abstract'


    #enterprise information
    enterprise_name = fields.Char('Enterprise Name')
    document_type = fields.Many2one('l10n_latam.identification.type','Document Type')
    identity_document = fields.Char('Identity Document')
    creation_date_enterprise = fields.Date('Creation Date')
    creation_place = fields.Date('Creation Place')
    group_name = fields.Char('Group Name')
    taxpayer_id = fields.Many2one('l10n_ec.taxpayer.type','Taxpayer Type')
    legal_person_name = fields.Char('Legal Representant Name')
    major_holder_name = fields.Char('Major Holder Name')
    enterprise_activity = fields.Text('List of activities')

    #address recent
    city = fields.Char('City')
    street = fields.Char('Street')
    sector = fields.Char('Sector')
    enterprise_telephone = fields.Char('Telephone')
    actual_time_address = fields.Integer('Address Time')
    number_of_places = fields.Integer('Number of Places')
    instalation_type = fields.Selection(INSTALLATION_TYPE,'Installation Type')
    enterprise_value = fields.Float('Enterprise Value')
    cost_place = fields.Float('Cost Place')

    #general information
    contact_person = fields.Char('Contact Person')
    contact_telephone = fields.Char('Contact Telephone')
    contact_cellphone = fields.Char('Contact Cellphone')
    contact_special_taxpayer = fields.Boolean('Contact Special Taxpayer')
    observations = fields.Text('Observations')
    croquis = fields.Binary('croquis')


