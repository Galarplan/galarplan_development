# -*- coding: utf-8 -*-
# from odoo import http


# class DailyPaymentReport(http.Controller):
#     @http.route('/daily_payment_report/daily_payment_report', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/daily_payment_report/daily_payment_report/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('daily_payment_report.listing', {
#             'root': '/daily_payment_report/daily_payment_report',
#             'objects': http.request.env['daily_payment_report.daily_payment_report'].search([]),
#         })

#     @http.route('/daily_payment_report/daily_payment_report/objects/<model("daily_payment_report.daily_payment_report"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('daily_payment_report.object', {
#             'object': obj
#         })
