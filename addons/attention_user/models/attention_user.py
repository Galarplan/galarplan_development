from odoo import models, fields, api


class AttentionUser(models.Model):
    _name = "attention.user"
    _description = "Customer Attention"
    _order = "date desc"

    company_id = fields.Many2one(
        "res.company",
        string="Compañia",
        required=True,
        copy=False,
        default=lambda self: self.env.company.id,
    )
    currency_id = fields.Many2one(related="company_id.currency_id", string="Moneda")
    date = fields.Datetime(string="Fecha, tiempo y hora", default=fields.Datetime.now)
    partner_id = fields.Many2one("res.partner", string="Cliente")
    group = fields.Char(string="Grupo")

    allowed_plan_ids = fields.Many2many(
        "account.saving",
        string="Planes permitidos",
        compute="_compute_allowed_plan_ids",
    )

    code_id = fields.Many2one(
        "account.saving",
        string="Plan de Ahorro",
        domain="[('id', 'in', allowed_plan_ids)]",
    )

    amount = fields.Monetary(string="Monto", compute="_compute_plan_data")
    start_date = fields.Date(string="Fecha Ingreso", compute="_compute_plan_data")
    total_payment = fields.Monetary(string="Valor Pagado", compute="_compute_plan_data")
    pending_amount = fields.Monetary(
        string="Valor Pendiente", compute="_compute_plan_data"
    )
    advisor_id = fields.Many2one("hr.employee", string="Asesor")
    commercial_manager_id = fields.Many2one("hr.employee", string="Jefe Comercial")
    concept_id = fields.Many2one(
        "attention.concept", string="Concepto", domain="[('active', '=', True)]"
    )
    detail = fields.Text(string="Detalle")
    doc = fields.Boolean(string="Doc")
    customer_service = fields.Text(string="Servicio al Cliente")
    document_ids = fields.One2many(
        "document.attention", "attention_id", string="Documentos"
    )

    @api.depends("partner_id")
    def _compute_allowed_plan_ids(self):
        for record in self:
            if record.partner_id:
                plans = self.env["account.saving"].search(
                    [("partner_id", "=", record.partner_id.id)]
                )
                record.allowed_plan_ids = plans
            else:
                record.allowed_plan_ids = False

    
    
    @api.onchange('partner_id')
    def _onchange_client_id(self):
        """Resetear el plan cuando cambia el cliente"""
        self.code_id = False
    
    
    @api.depends('code_id', 'code_id.por_pagar', 'code_id.start_date', 'code_id.pagos', 'code_id.pendiente')
    def _compute_plan_data(self):
        for record in self:
            if not record.code_id:
                record.update({
                    'amount': 0.0,
                    'start_date': False,
                    'total_payment': 0.0,
                    'pending_amount': 0.0,
                })
            else:
                record.update({
                    'amount': record.code_id.por_pagar or 0.0,
                    'start_date': record.code_id.start_date,
                    'total_payment': record.code_id.pagos or 0.0,
                    'pending_amount': record.code_id.pendiente or 0.0,
                })

