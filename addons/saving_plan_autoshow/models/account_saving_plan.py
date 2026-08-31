from odoo import _, api, fields, models

class AccountSavingPlan(models.Model):
    _inherit = 'account.saving.plan'


    percent_big_quote = fields.Float('Cuota Premiun')

    saving_type = fields.Selection([('normal','Normal'),('ballon','Ballon'),('premiun','Premium'),('flex','Flex')],default='normal')

    with_aditions = fields.Boolean('Adicionales',default=False)

    iva_amount_percent = fields.Float('IVA Plan',default=0.0)

    gl_legal = fields.Float('Gasto Legal',default=0.0)

    device_value = fields.Float('Dispositivo',default=0.0)

    def action_draft_state(self):
        for record in self:
            record.state = 'draft'
