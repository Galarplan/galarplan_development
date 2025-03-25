from odoo import http
from odoo.http import request, Response
import json
from odoo import fields
from odoo.service import db  # Importar el módulo db para manejar conexiones manualmente
from odoo.sql_db import db_connect  # Importar db_connect para obtener el cursor

# @http.route('/api/create_ticket', type='json', auth='user', methods=['POST'], csrf=False)

class ModalImagenes(http.Controller):

    
    # @http.route('/api/imagenes', type='http', auth='public', methods=['OPTIONS'], cors='*', csrf=False)
    # def handle_options(self, **kwargs):
    #     print('==========================opciones')
    #     headers = {
    #         'Access-Control-Allow-Origin': '*',
    #         'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    #         'Access-Control-Allow-Headers': 'Origin, Content-Type, Accept',
    #         'Access-Control-Max-Age': '86400',  # Cache preflight request for 1 day
    #     }
    #     return Response(status=200, headers=headers)
    
    # Controlador para obtener imágenes
    @http.route(['/api/imagenes'], auth='none',type='http', methods=['GET'], cors='*', csrf=False)
    def obtener_imagenes(self, **kwargs):
        
        print('===================================lllamdoooo')
        try:
            # Verificar la base de datos actual
            db = kwargs.get('db')
            request.session.db = db
            print(f"Base de datos actual: {request.session.db}")  # Depuración

            print('===================================lllamdoooo2')
            with db_connect(db).cursor() as cr:
                query = """
                    SELECT gti.id, gti.nombre, gti.descripcion, 
                           (CASE WHEN ia.id IS NOT NULL THEN TRUE ELSE FALSE END) as tiene_imagen
                    FROM generador_turnos_imagen gti
                    LEFT JOIN ir_attachment ia 
                        ON ia.res_model = 'generador_turnos.imagen' 
                        AND ia.res_field = 'imagen' 
                        AND ia.res_id = gti.id
                """
                cr.execute(query)
                imagenes = cr.fetchall()
                print('======================================IMG', imagenes)

                # Construir la lista de resultados
                imagen_list = []
                for imagen in imagenes:
                    imagen_list.append({
                        'id': imagen[0],  # id
                        'nombre': imagen[1],  # nombre
                        'descripcion': imagen[2],  # descripcion
                        'imagen_url': f'/web/image/generador_turnos.imagen/{imagen[0]}/imagen' if imagen[3] else None,  # tiene_imagen
                    })

            return http.Response(
                json.dumps(imagen_list),
                content_type='application/json',
                # headers=[('Access-Control-Allow-Origin', '*')]
            )
        except Exception as e:
            print(f"Error en la ejecución: {str(e)}")
            return http.Response(
                json.dumps({'error': str(e)}),
                content_type='application/json',
                status=500,
                # headers=[('Access-Control-Allow-Origin', '*')]
            )