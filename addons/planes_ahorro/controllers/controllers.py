# -*- coding: utf-8 -*-
# from odoo import http


# class PlanesAhorro(http.Controller):
#     @http.route('/planes_ahorro/planes_ahorro', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/planes_ahorro/planes_ahorro/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('planes_ahorro.listing', {
#             'root': '/planes_ahorro/planes_ahorro',
#             'objects': http.request.env['planes_ahorro.planes_ahorro'].search([]),
#         })

#     @http.route('/planes_ahorro/planes_ahorro/objects/<model("planes_ahorro.planes_ahorro"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('planes_ahorro.object', {
#             'object': obj
#         })
