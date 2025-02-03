# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _, SUPERUSER_ID


class HrEmployeePaymentLine(models.Model):
    _name = "hr.employee.payment.line"
    _description = "Detalle de Pagos a  Empleados"

    process_id=fields.Many2one("hr.employee.payment","Proceso",ondelete="cascade")

    name = fields.Char("Descripción", size=255, required=True)

    company_id = fields.Many2one("res.company", string="Compañia", related="process_id.company_id",store=False,readonly=True)
    currency_id = fields.Many2one("res.currency", "Moneda",related="company_id.currency_id",store=False,readonly=True)

    employee_id = fields.Many2one("hr.employee", "Empleado", required=True)
    total = fields.Monetary("Valor", digits=(16, 2), default=0.01, required=True)

    bank_account_id = fields.Many2one("res.partner.bank", "Cuenta de Banco", required=False)

    bank_id = fields.Many2one("res.bank", "Banco")
    bank_acc_number = fields.Char("# Cuenta")
    bank_tipo_cuenta = fields.Selection([('Corriente', 'Corriente'),
                                         ('Ahorro', 'Ahorro'),
                                         ('Tarjeta', 'Tarjeta'),
                                         ('Virtual', 'Virtual')
                                         ], string="Tipo de Cuenta")

    _order = "process_id desc,employee_id asc"