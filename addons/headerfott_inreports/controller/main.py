from odoo import http
from odoo.http import request, content_disposition
import json

class CustomAccountReportController(http.Controller):

    @http.route('/account_reports', type='http', auth='user', methods=['POST'], csrf=False)
    def get_report(self, options, file_generator, **kwargs):
        # Lógica personalizada antes de llamar al controlador original
        print("==============================================Este es mi controlador personalizado")

        # Llamar al controlador original (si es necesario)
        original_controller = request.env['ir.http']._get_controller_class('account_reports')
        return original_controller().get_report(options, file_generator, **kwargs)