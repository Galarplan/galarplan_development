# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api,fields, models,_
from odoo.exceptions import ValidationError,UserError
from ...calendar_days.tools import CalendarManager,DateManager,MonthManager

dtObj = DateManager()

class HrPayslipInput(models.Model):
    _inherit="hr.payslip.input"

    input_type_id = fields.Many2one('hr.payslip.input.type', string='Tipo', required=False,
                                    domain="['|', ('id', 'in', _allowed_input_type_ids), ('struct_ids', '=', False)]")
    rule_id = fields.Many2one('hr.salary.rule', string='Rubro', required=False)
    category_id = fields.Many2one('hr.salary.rule.category', string='Categoría',required=True)
    category_code = fields.Char(related="category_id.code", store=False, readonly=True)

    code = fields.Char(string="Código")
    movement_id = fields.Many2one("hr.employee.movement.line", "Movimiento", required=True)

    original_amount = fields.Monetary("Monto Original", digits=(16, 2), required=True)
    original_pending = fields.Monetary("Pendiente Original", digits=(16, 2), required=True)

    amount = fields.Monetary("Monto", digits=(16, 2), required=True)
    add_iess = fields.Boolean("Agregar IESS", default=False)

    movement_ref_id=fields.Char("# Referencia",required=True)
    date_process = fields.Date("Fecha de Vencimiento",  required=True)
    quota = fields.Integer(string="Cuota", default=1, required=True)
    force_payslip=fields.Boolean("Forzar en Rol",default=False)

    currency_id=fields.Many2one(string="Moneda",related="payslip_id.currency_id",store=False,readonly=True)

    def unlink(self):
        move_lines = self.env["hr.employee.movement.line"]
        # Mapeo de movement_id de todos los registros
        move_lines += self.mapped('movement_id')
        # Llamar al metodo unlink del superclase
        values = super(HrPayslipInput, self).unlink()
        # Calcular total solo si hay líneas de movimiento
        if move_lines:
            move_lines._compute_total()
        return values

    @api.onchange('amount')
    def onchange_amount(self):
        warning={}
        if not self.amount or self.amount<=0:
            self.amount=self.original_pending
            warning={"title":_("Advertencia"),
                     "message":_("El monto aplicado debe ser mayor a 0.00 ,referencia %s") % (self.movement_ref_id,)
                     }
        if self.amount>self.original_pending:
            self.amount=self.original_pending
            warning={"title":_("Advertencia"),
                     "message":_("El monto aplicado NO puede ser mayor al valor pendiente original %s ,referencia %s") % (self.original_pending,self.movement_ref_id,)
                     }
        if warning:
            return {"warning":warning}

    _order="category_id asc,rule_id asc,amount asc"
