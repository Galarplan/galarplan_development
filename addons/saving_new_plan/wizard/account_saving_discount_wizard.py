from odoo import models, fields

from odoo import models, fields

print("********** CARGANDO account_saving_discount_wizard.py **********")

class AccountSavingDiscountWizard(models.TransientModel):
    _name = 'account.saving.discount.wizard'
    _description = 'Confirmación de descuento'

    saving_id = fields.Many2one(
        'account.saving',
        string='Plan de ahorro'
    )

    percent_discount = fields.Float(
        string='Porcentaje descuento'
    )


    def action_confirm_discount(self):
        self.ensure_one()

        saving = self.saving_id

        # actualizar porcentaje antes de aplicar
        saving.percent_discount = self.percent_discount

        # ejecutar tu lógica actual
        saving.apply_discount_values()

        return {'type': 'ir.actions.act_window_close'}