
from odoo import models, fields, api, _

DOCUMENT_TYPE = [('ruc','RUC'),('ci','CI'),('passport','Passport')]
SEX_TYPE = [('F','Female'),('M',"Male")]
CIVIL_STATE = [('married','Married'),('single','Single')]

class CustomerCreditRequest(models.Model):
    _name = 'customer.request'
    _description = 'customer credit request'
    _inherit = 'credit.request.abstract'

    #personal information
    personal_name = fields.Char('Personal Name')
    first_last_name = fields.Char('First Last Name')
    second_last_name = fields.Char('Second Last Name')
    identity_document = fields.Char('Identity Document')
    document_type = fields.Many2one('l10n_latam.identification.type','Document Type')
    sex_type = fields.Selection(SEX_TYPE,'Sex')
    age = fields.Integer('Age')
    birthday = fields.Date('Birthday')
    nationality = fields.Char('Nationality')
    civil_state = fields.Selection(CIVIL_STATE,'Maritla Status')
    separation_actives = fields.Boolean('Separation')
    own_house = fields.Boolean('House')
    own_ground = fields.Boolean('Ground')
    own_vehicle  = fields.Boolean('vehicle')
    own_assets = fields.Boolean('Assets')
    own_bussiness = fields.Boolean('Buisness')
    own_bussiness_assets = fields.Boolean('Business Assets')
    address = fields.Char('Address')
    telephone = fields.Char('Telephone')
    city = fields.Char('City')
    house_time = fields.Integer('Contract house Time')
    house_contract_people_name = fields.Char('House Name')
    telephone_house = fields.Char('Telephone House')

    #economic activity info
    work_place = fields.Char('Work Place')
    Work_adderss = fields.Char('Work Address')
    work_telephone = fields.Char('Work Telephone')
    work_hr_name = fields.Char('Work Human Resource Boos')
    work_time = fields.Char('Work Time')
    work_name = fields.Char('Work Name')
    last_work_place = fields.Char('last Work place')

    #conyuge information
    conyuge_personal_name = fields.Char('Personal Name')
    conyuge_first_last_name = fields.Char('First Last Name')
    conyuge_second_last_name = fields.Char('Second Last Name')
    conyuge_identity_document = fields.Char('Identity Document')
    conyuge_document_type = fields.Selection(DOCUMENT_TYPE,'Document Type')
    conyuge_sex_type = fields.Selection(SEX_TYPE,'Sex')
    conyuge_age = fields.Integer('Age')
    conyuge_birthday = fields.Date('Birthday')
    conyuge_nationality = fields.Char('Nationality')
    conyuge_work_place = fields.Char('Work Place')
    conyuge_Work_adderss = fields.Char('Work Address')
    conyuge_work_telephone = fields.Char('Work Telephone')
    conyuge_work_time = fields.Char('Work Time')
    conyuge_work_name = fields.Char('Work Name')

    assets_details = fields.Html('assets_details')
    croquis = fields.Binary('croquis')
