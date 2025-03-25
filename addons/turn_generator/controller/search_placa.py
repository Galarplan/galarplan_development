from odoo import http
from odoo.http import request, Response
import json
from odoo.service import db
from odoo.sql_db import db_connect


class VehiculoController(http.Controller):

    @http.route(
        "/api/buscar_placa",
        type="http",
        auth="none",
        methods=["GET"],
        cors="*",
        csrf=False,
    )
    def buscar_placa(self, **kwargs):
        try:
            db = kwargs.get("db")  # Obtener la base de datos de los parámetros
            placa = kwargs.get("placa")  # Obtener la placa de los parámetros
            if not db or not placa:
                return Response(
                    json.dumps({"error": "Se requieren los parámetros 'db' y 'placa'"}),
                    content_type="application/json",
                    status=400,  # Bad Request
                )

            request.session.db = db
            with db_connect(db).cursor() as cr:
                # Consulta SQL para buscar el vehículo por placa
                query = """
                    SELECT 
                        placa,
                        nombre,
                        correo,
                        identificacion,
                        modelo,
                        marca
                    FROM generador_turnos_vehiculo
                    WHERE placa = %s;
                """
                cr.execute(query, (placa,))
                vehiculo = cr.fetchone()

                if not vehiculo:
                    return Response(
                        json.dumps({"error": "Vehículo no encontrado"}),
                        content_type="application/json",
                        status=404,  # Not Found
                    )

                # Construir el diccionario con los datos del vehículo
                datos_vehiculo = {
                    "placa": vehiculo[0],
                    "nombre": vehiculo[1],
                    "correo": vehiculo[2],
                    "identificacion": vehiculo[3],
                    "modelo": vehiculo[4],
                    "marca": vehiculo[5],
                }

            return Response(
                json.dumps(datos_vehiculo),
                content_type="application/json",
                status=200,  # OK
            )

        except Exception as e:
            print(f"Error en la ejecución: {str(e)}")
            return Response(
                json.dumps({"error": str(e)}),
                content_type="application/json",
                status=500,  # Internal Server Error
            )