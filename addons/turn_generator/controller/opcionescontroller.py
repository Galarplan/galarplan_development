from odoo import http
from odoo.http import request, Response
import json
from odoo.service import db  # Importar el módulo db para manejar conexiones manualmente
from odoo.sql_db import db_connect  # Importar db_connect para obtener el cursor


class OpcionesController(http.Controller):

        # Controlador para obtener opciones
    @http.route('/api/opciones', type='http', auth='none', methods=['GET'], cors='*', csrf=False)
    def obtener_opciones(self, **kwargs):
        try:
            db = kwargs.get('db')
            request.session.db = db
            print(f"Base de datos actual: {request.session.db}")  # Depuración
            with db_connect(db).cursor() as cr:
                query = """
                    SELECT gto.id, gto.nombre, gto.descripcion, 
                           (CASE WHEN ia.id IS NOT NULL THEN TRUE ELSE FALSE END) as tiene_imagen,
                           gto.slug as enlace
                    FROM generador_turnos_opcion gto 
                    LEFT JOIN ir_attachment ia 
                        ON ia.res_model = 'generador_turnos.opcion' 
                        AND ia.res_field = 'imagen' 
                        AND ia.res_id = gto.id
                """
                cr.execute(query)
                opciones = cr.fetchall()

                # Construir la lista de resultados
                opciones_list = []
                for opcion in opciones:
                    opciones_list.append({
                        'id': opcion[0],  # id
                        'nombre': opcion[1],  # nombre
                        'descripcion': opcion[2],  # descripcion
                        'imagen_url': f'/web/image/generador_turnos.opcion/{opcion[0]}/imagen' if opcion[3] else None,  # tiene_imagen
                        'enlace':opcion[4],
                    })

            return http.Response(
                json.dumps(opciones_list),
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

            
            