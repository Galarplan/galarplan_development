from odoo import models, fields

class KnowYourCustomer(models.Model):
    _name = 'know.your.customer'
    _description = 'Know Your Customer'

    # 1. customer information
    name = fields.Char(string="Razón Social", required=True)
    identification_type = fields.Selection([
        ('cedula', 'Cédula'),
        ('ruc', 'RUC'),
        ('pasaporte', 'Pasaporte')
    ], string="Tipo de Identificación", required=True)
    identification_number = fields.Char(string="Número de Identificación", required=True)
    nationality = fields.Char(string="Nacionalidad")
    birth_date = fields.Date(string="Fecha de Nacimiento / Constitución")
    country = fields.Many2one('res.country',string='Pais')
    provincia = fields.Many2one('res.country.state',string = 'Provincia')
    city = fields.Char(string='Ciudad')
    main_street = fields.Char(string='Calle Principal')
    cellphone = fields.Char(string='celular')

    # 3. informacion del conyuge/representante legal
    conyuge_name = fields.Char('Nombre completo')
    conyuge_identity_document = fields.Char('Documento de identidad')
    conyuge_document_type = fields.Selection([
        ('cedula', 'Cédula'),
        ('ruc', 'RUC'),
        ('pasaporte', 'Pasaporte')
    ], string="Tipo de Identificación", required=True)
    conyuge_economic_activity = fields.Text(string="Actividad Económica")
    conyuge_monthly_income = fields.Float(string="Ingresos Mensuales")

    # 4. actividad economica/ocupacion
    origin_incomes = fields.Char('Origen de ingresos mensuales')
    economic_activity = fields.Text(string="Actividad Económica")
    
    #5.informacion de socios o accionistas
    line_ids = fields.One2many('know.customer.partner.info.line','line_id', string='Socios/Accionistas')

    
    #6. informacion economica
    monthly_income = fields.Float(string="Ingresos Mensuales")
    assets_sum = fields.Float(string='Total de Activos')
    monthly_expenses = fields.Float(string="Egresos Mensuales")
    other_incomes = fields.Boolean(string='Posee Ingresos Diferentes a la actividad principal descrita anteriormente?')
    other_funds = fields.Char(string='Fuente de ingresos diferente a la actividad economica')
    other_incomes = fields.Float(string='Otros Ingresos')

    # 7 vinculos entre cleinte y beneficiario
    benefict_name = fields.Char(string='Razon social o nombres completos del beneficiario')
    benefict_birth_date = fields.Char(string='Fecha Constitucion/Nacimineto')
    benefict_cellpone = fields.Char(string='Celular')
    benefict_identity = fields.Char(string='Numero de identificacion')
    benefict_nationality = fields.Char(string='Nacionalidad')
    benefict_street = fields.Char(string='Direccion')
    benefict_mail = fields.Char(string='Correo Electronico')
    benefict_relation = fields.Char(string='Relacion')
    benefict_telephone = fields.Char('Telefono')
    benefict_relation_other = fields.Char('Explique la relacion en caso de otro')

    payment_name = fields.Char(string='Razon social o nombres completos del beneficiario')
    payment_birth_date = fields.Char(string='Fecha Constitucion/Nacimineto')
    payment_cellpone = fields.Char(string='Celular')
    payment_identity = fields.Char(string='Numero de identificacion')
    payment_nationality = fields.Char(string='Nacionalidad')
    payment_street = fields.Char(string='Direccion')
    payment_mail = fields.Char(string='Correo Electronico')
    payment_relation = fields.Char(string='Relacion')
    payment_telephone = fields.Char('Telefono')
    payment_relation_other = fields.Char('Explique la relacion en caso de otro:')

    #8 declaracion y vinculacion
    company_family = fields.Boolean('Tiene algun familiar que labore en la empresa')
    politically_exposed = fields.Boolean(string="Persona Expuesta Políticamente")
    family_politically_exposed = fields.Boolean(string="Familiar con Persona Expuesta Políticamente")
    parent_person_company = fields.Char('Parentesco')
    company_job_family = fields.Char('Cargo que desempeña/Institucion')
    own_company_family = fields.Char('Cargo que desempeña/Institucion')
    job = fields.Char('Cargo que desempeña')

    #11 Justificacion por no obtencion de datos
    justification = fields.Text('Justificacion No datos')

    #14 persona que recepta la informacion
    responsible_name = fields.Char(string="Nombre del Responsable")
    responsible_id = fields.Char(string="Número de Identificación del Responsable")
    responsible_job = fields.Char('Cargo')
    reponsible_city = fields.Char('Ciudad')
    reponsible_date = fields.Date('Fecha')

    

    declaration = fields.Text(string="Declaración")
    documents = fields.Text(string="Documentos Entregados")
    approval_date = fields.Date(string="Fecha de Aprobación")
    approved_by = fields.Many2one('res.users', string="Aprobado por")

class PartnerInfoLine(models.Model):
    _name = 'know.customer.partner.info.line'
    _description = ' provider lines'

    line_id = fields.Many2one('know.your.customer', string='Socios', ondelete='cascade')

    complete_name = fields.Char(string='Nombre Completos')
    identification = fields.Char(string='Identificacion')
    participation_percent = fields.Float(string='% Participacion')
    economic_activity = fields.Char(string='Actividad Economica')

