from odoo import models, fields

class FiduciaForms(models.Model):
    _name = 'fiducia.forms'
    _description = 'Formulario de Fiducia'

    # Sección 1: Datos Personales
    primer_apellido = fields.Char(string='Primer Apellido')
    segundo_apellido = fields.Char(string='Segundo Apellido')
    nombres = fields.Char(string='Nombres')
    cedula = fields.Char(string='Número de Cédula')
    nacionalidad = fields.Char(string='Nacionalidad')
    fecha_nacimiento = fields.Date(string='Fecha de Nacimiento')
    estado_civil = fields.Selection([
        ('soltero', 'Soltero'),
        ('casado', 'Casado'),
        ('divorciado', 'Divorciado'),
        ('viudo', 'Viudo')
    ], string='Estado Civil')
    pais = fields.Char(string='País')
    provincia = fields.Char(string='Provincia')
    canton = fields.Char(string='Cantón')
    direccion = fields.Char(string='Dirección')
    celular = fields.Char(string='Celular')
    correo_electronico = fields.Char(string='Correo Electrónico')

    # Sección 2: Lugar de Trabajo
    # Comentario: Información laboral y actividad económica
    tipo_relacion_laboral = fields.Selection([
        ('dependiente_privado', 'Dependiente Sector Privado'),
        ('independiente_profesional', 'Independiente Profesional'),
        ('independiente_no_profesional', 'Independiente No Profesional'),
        ('dependiente_publico', 'Dependiente Sector Público'),
        ('no_labora', 'No Labora')
    ], string='Tipo de Relación Laboral')
    actividad_economica = fields.Char(string='Actividad Económica')

    # Sección 3: Residencia Fiscal
    es_estadounidense = fields.Boolean(string='¿Es Estadounidense para fines fiscales?')
    residente_otro_pais = fields.Boolean(string='¿Es residente de otro país?')
    pais_residencia = fields.Char(string='País de Residencia')

    # Sección 4: Información Patrimonial
    total_activos = fields.Float(string='Total Activos')
    total_pasivos = fields.Float(string='Total Pasivos')
    total_patrimonio = fields.Float(string='Total Patrimonio')

    # Sección 5: Información Financiera
    ingresos_principales = fields.Float(string='Ingresos por Actividad Principal')
    otros_ingresos = fields.Float(string='Otros Ingresos')
    total_ingresos_mensuales = fields.Float(string='Total Ingresos Mensuales')
    total_egresos_mensuales = fields.Float(string='Total Egresos Mensuales')

    # Sección 6: Origen de Bienes
    origen_bienes = fields.Char(string='Origen de Bienes o Recursos')

    # Sección 7: Referencias Bancarias - One2many
    referencia_bancaria_ids = fields.One2many(
        'fiducia.referencia.bancaria', 'fiducia_id', string='Referencias Bancarias'
    )

    # Sección 8: Persona Expuesta Políticamente
    es_pep = fields.Boolean(string='¿Es Persona Expuesta Políticamente?')
    nombre_pep = fields.Char(string='Nombre del PEP')
    cargo_pep = fields.Char(string='Cargo del PEP')
    relacion_pep = fields.Char(string='Relación con la Persona Expuesta')
    institucion_pep = fields.Char(string='Institución')
    fecha_inicio_pep = fields.Date(string='Fecha de Inicio de Funciones')
    fecha_fin_pep = fields.Date(string='Fecha de Finalización de Funciones')

    # Sección 9: Declaración de Vinculación
    vinculacion_fiducia = fields.Boolean(string='¿Tiene vinculación con Fiducia S.A.?')
    detalle_vinculacion = fields.Text(string='Detalle de Vinculación')


class FiduciaReferenciaBancaria(models.Model):
    _name = 'fiducia.referencia.bancaria'
    _description = 'Referencias Bancarias de Fiducia'

    fiducia_id = fields.Many2one('fiducia.forms', string='Formulario Fiducia')
    institucion = fields.Char(string='Institución Financiera')
    tipo_cuenta = fields.Selection([
        ('corriente', 'Corriente'),
        ('ahorros', 'Ahorros')
    ], string='Tipo de Cuenta')
    numero_cuenta = fields.Char(string='Número de Cuenta')
