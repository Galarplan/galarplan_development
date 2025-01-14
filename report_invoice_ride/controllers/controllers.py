# -*- coding: utf-8 -*-
# from odoo import http


# class ReportInvoiceRide(http.Controller):
#     @http.route('/report_invoice_ride/report_invoice_ride', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/report_invoice_ride/report_invoice_ride/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('report_invoice_ride.listing', {
#             'root': '/report_invoice_ride/report_invoice_ride',
#             'objects': http.request.env['report_invoice_ride.report_invoice_ride'].search([]),
#         })

#     @http.route('/report_invoice_ride/report_invoice_ride/objects/<model("report_invoice_ride.report_invoice_ride"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('report_invoice_ride.object', {
#             'object': obj
#         })
