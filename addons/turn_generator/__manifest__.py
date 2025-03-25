{
    'name': 'Generador de Turnos',
    'version': '1.0',
    'summary': 'Módulo para generar turnos basados en placas de vehículos',
    'description': 'Este módulo permite gestionar vehículos, generar turnos y asociar imágenes y opciones.',
    'author': 'Tu Nombre',
    'depends': ['base','web','turnos'],
    'data': [
        'security/ir.model.access.csv',
        'views/vehiculo_views.xml',
        'views/turno_views.xml',
        'views/tramite_views.xml',
        'views/imagen_views.xml',
        'views/opcion_views.xml',
    ],
    'installable': True,
    'application': True,
}