from odoo import models, fields, api, _

class ReceiptPlan(models.Model):
    _name = 'receipt.saving.plan.view'
    _description = 'Recibo de pago para los usuarios de caja'
    _auto = False

    nombre_plan = fields.Char(string='Nombre del Plan')
    ahorro = fields.Float(string='Ahorro')
    name = fields.Char(string='Nombre de Línea')
    partner_name = fields.Char(string='Nombre del Socio')
    partner_vat = fields.Char(string='RUC/Cédula')
    partner_id = fields.Many2one('res.partner', string='Socio')
    invoice_name = fields.Char(string='Factura')
    authorization_type = fields.Char(string='Número de Autorización')
    last_payment = fields.Date(string='Último Pago')
    deposit_partner = fields.Date(string='Fecha de Depósito')
    payment = fields.Float(string='Pago')
    cap = fields.Float(string='Capital')
    adm_waste_1 = fields.Float(string='Administración/Residuos 1')
    adm_waste_2 = fields.Float(string='Administración/Residuos 2')
    pending_cap = fields.Float(string='Capital Pendiente')
    currency_id = fields.Many2one('res.currency', string='Moneda', readonly=True)


     # Hacer todos los campos readonly a nivel de modelo
    def _readonly_fields(self):
        return self._fields.keys()
    
    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super(ReceiptPlan, self).fields_get(allfields, attributes=attributes)
        for field in res:
            res[field]['readonly'] = True
        return res

    # def print_receipt(self):
    #     self.ensure_one()
    #     return {
    #         'type': 'ir.actions.report',
    #         'report_name': 'saving_plan_receipt.report_receipt_saving_plan',
    #         # 'report_type': 'qweb-pdf',
    #         'report_type': 'qweb-html',
    #         'docs': self,
    #         'context': {
    #             'discard_logo_check': True,
    #             'default_currency_id': self.currency_id.id  # Asegura que la moneda esté disponible
    #         },
    #     }
    def print_receipt(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.report',
            'report_name': 'saving_plan_receipt.report_receipt_saving_plan',
            'report_type': 'qweb-html',
            'docs': self,
            'context': {
                'discard_logo_check': True,
                'default_currency_id': self.currency_id.id,
                'active_model': self._name,
                'active_id': self.id,
                'company': self.env.company,   # Asegura que la compañía está en el contexto
            },
        }

    def init(self):
        self.env.cr.execute("""DROP VIEW IF EXISTS receipt_saving_plan_view;""")
        self.env.cr.execute("""
            create view receipt_saving_plan_view as
            select 
                asl.id   as id,
                sa."name" as nombre_plan,
                sa.saving_amount as ahorro,
                asl."name",
                rp."name" as partner_name,
                rp.vat as partner_vat,
                asl.partner_id as partner_id,
                coalesce(am2."name",'Migrado') as invoice_name,
                coalesce(am2.l10n_ec_authorization_number,'Migrado') as authorization_type,
                asl.last_payment_date as last_payment,
                asl.deposit_date as deposit_partner,
                asl.saving_amount as payment,
                asl.principal_amount as cap,
                asl.serv_admin_amount as adm_waste_1,
                asl.seguro_amount as adm_waste_2,
                sa.pendiente as pending_cap,
                rc.id as currency_id  -- Añade la moneda de la compañía
            from account_saving_lines as asl 
            left join account_saving as sa on sa.id = asl.saving_id 
            left join res_partner as rp on rp.id = asl.partner_id
            left join account_move as am2 on am2.id = asl.invoice_id 
            left join res_company rc on rc.id = am2.company_id  -- O usa la compañía que corresponda
            where asl.estado_pago = 'pagado'
        """)
    