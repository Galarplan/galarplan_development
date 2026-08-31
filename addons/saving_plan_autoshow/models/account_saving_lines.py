from odoo import _, api, fields, models

class AccountSavingLines(models.Model):
    _inherit = 'account.saving.lines'

    gl_mensual = fields.Float('Gl Mensual')

    disp_mensual = fields.Float('Disp Mensual')


    # saving_type = fields.Selection(
    #     string="Tipo de Plan",
    #     related='saving_id.saving_type',
    #     store=True,
    #     readonly=True
    # )