from odoo import http
from odoo.http import request, Response
import json
from odoo.service import db
from odoo.sql_db import db_connect


class ServiciosDetallesController(http.Controller):

    @http.route(
        "/api/servicios",
        type="http",
        auth="none",
        methods=["GET"],
        cors="*",
        csrf=False,
    )
    def obtener_detalles_servicios(self, **kwargs):
        try:
            db = kwargs.get("db")
            opcion = kwargs.get("op")
            request.session.db = db
            with db_connect(db).cursor() as cr:
                # Obtener el trámite con sus líneas relacionadas
                query = f"""
                    SELECT 
                        tr.id, 
                        tr.service_name, 
                        tr.have_services, 
                        tr.have_requeriments, 
                        tr.have_payments,
                        tsl.name AS servicio_nombre,
                        trl.name AS requisito_nombre,
                        tp.product_id, 
                        pt.name->'es_EC' AS producto_nombre,  -- Nombre del producto desde product_template
                        tp.costo
                    FROM tramite_root tr
                    LEFT JOIN tramite_service_line tsl ON tr.id = tsl.tramite_id
                    LEFT JOIN tramite_requeriments_line trl ON tr.id = trl.tramite_id
                    LEFT JOIN tramite_products tp ON tr.id = tp.tramite_id
                    LEFT JOIN product_product pp ON tp.product_id = pp.id  -- Unión con product_product
                    LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id  -- Unión con product_template
                    WHERE tr.opcion_id = {opcion};
                """
                cr.execute(query)
                tramites = cr.fetchall()

                # Construir la lista de resultados
                tramites_dict = {}
                for tramite in tramites:
                    tramite_id = tramite[0]
                    if tramite_id not in tramites_dict:
                        tramites_dict[tramite_id] = {
                            "id": tramite_id,
                            "service_name": tramite[1],
                            "have_services": tramite[2],
                            "have_requeriments": tramite[3],
                            "have_payments": tramite[4],
                            "tramite_lines": [],
                            "tramite_requeriment_lines": [],
                            "tramite_produt_lines": [],
                        }

                    # Agregar servicios únicos
                    if tramite[5]:  # servicio_nombre
                        servicio = {"name": tramite[5]}
                        if servicio not in tramites_dict[tramite_id]["tramite_lines"]:
                            tramites_dict[tramite_id]["tramite_lines"].append(servicio)

                    # Agregar requisitos únicos
                    if tramite[6]:  # requisito_nombre
                        requisito = {"name": tramite[6]}
                        if (
                            requisito
                            not in tramites_dict[tramite_id][
                                "tramite_requeriment_lines"
                            ]
                        ):
                            tramites_dict[tramite_id][
                                "tramite_requeriment_lines"
                            ].append(requisito)

                    # Agregar productos únicos
                    if tramite[7]:  # product_id
                        producto = {
                            "product_id": tramite[7],
                            "producto_nombre": tramite[8],  # Nombre del producto
                            "costo": tramite[9],
                        }
                        if (
                            producto
                            not in tramites_dict[tramite_id]["tramite_produt_lines"]
                        ):
                            tramites_dict[tramite_id]["tramite_produt_lines"].append(
                                producto
                            )

                tramites_list = list(tramites_dict.values())

            return http.Response(
                json.dumps(tramites_list),
                content_type="application/json",
            )
        except Exception as e:
            print(f"Error en la ejecución: {str(e)}")
            return http.Response(
                json.dumps({"error": str(e)}),
                content_type="application/json",
                status=500,
            )
