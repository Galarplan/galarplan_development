from odoo import models, fields, api
from odoo.tools import format_date


class ContractContract(models.Model):
    _inherit = "contract.contract"

    payment_count = fields.Integer(
        string="Payments Count",
        compute="_compute_payment_count",
        store=False,
    )
    number_of_installments = fields.Integer(
        string="Cuotas", help="Indica el numero de cuotas del contrato"
    )

    plan_type = fields.Selection(
        selection=[
            ("ahorros", "Ahorros"),
            ("financiamiento", "Financiamiento"),
        ],
        string="Tipo de Plan",
    )

    plan_code = fields.Char("Codigo")

    amount_plan = fields.Float("Importe del plan")

    def action_print_account_statement(self):
        self.ensure_one()

        # Generar el PDF usando un reporte QWeb
        return self.env.ref(
            "contract_extension.action_report_account_statement"
        ).report_action(self)

    @api.depends("invoice_count")
    def _compute_payment_count(self):
        for record in self:
            # Obtener facturas relacionadas al contrato
            related_invoices = record._get_related_invoices()
            # Obtener líneas de apuntes contables de las facturas
            invoice_lines = related_invoices.mapped("line_ids")
            # Obtener los apuntes contables de los pagos mediante reconciliaciones
            payment_lines = self.env["account.move.line"].search(
                [
                    ("matched_debit_ids.debit_move_id", "in", invoice_lines.ids),
                    (
                        "payment_id",
                        "!=",
                        False,
                    ),  # Asegurarse de que esté relacionado con un pago
                ]
            )
            # Obtener los pagos relacionados
            payments = payment_lines.mapped("payment_id")
            record.payment_count = len(payments)

    def action_show_payments(self):
        self.ensure_one()
        tree_view = self.env.ref(
            "account.view_account_payment_tree", raise_if_not_found=False
        )
        form_view = self.env.ref(
            "account.view_account_payment_form", raise_if_not_found=False
        )
        # Obtener facturas relacionadas
        related_invoices = self._get_related_invoices()
        # Obtener líneas de apuntes contables de las facturas
        invoice_lines = related_invoices.mapped("line_ids")
        # Obtener los apuntes contables de los pagos mediante reconciliaciones
        payment_lines = self.env["account.move.line"].search(
            [
                ("matched_debit_ids.debit_move_id", "in", invoice_lines.ids),
                ("payment_id", "!=", False),
            ]
        )
        # Obtener los pagos relacionados
        payments = payment_lines.mapped("payment_id")
        action = {
            "type": "ir.actions.act_window",
            "name": "Payments",
            "res_model": "account.payment",
            "view_mode": "tree,form",
            "domain": [("id", "in", payments.ids)],
        }
        if tree_view and form_view:
            action["views"] = [(tree_view.id, "tree"), (form_view.id, "form")]
        return action
