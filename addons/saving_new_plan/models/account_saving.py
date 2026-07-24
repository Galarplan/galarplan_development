from odoo import _, api, fields, models
from dateutil.relativedelta import relativedelta

class AccountSaving(models.Model):
    _inherit = 'account.saving'

    enable_discount = fields.Boolean('Habilitar')
    percent_discount = fields.Float('Descuento')
    last_date = fields.Date('new date')

   

    @api.onchange('enable_discount', 'percent_discount')
    def _compute_discount_values(self):
        """Calcula los valores de descuento para la cuota 0"""
        for saving in self:
            # Buscar la cuota 0 (number=0)
            quota_zero = saving.line_ids.filtered(lambda l: l.number == 0)
            print('=====================',quota_zero)
            if quota_zero:
                if saving.enable_discount and saving.percent_discount > 0:
                    # Calcular el descuento
                    original_amount = quota_zero.serv_inscription_amount
                    if quota_zero.last_serv_inscription_amount == 0:
                        # Si no tiene valor guardado, guardar el original
                        quota_zero.last_serv_inscription_amount = original_amount
                    
                    # Aplicar descuento
                    discount_amount = original_amount * (saving.percent_discount / 100)
                    quota_zero.serv_inscription_amount = original_amount - discount_amount
                    quota_zero.discount = saving.percent_discount
                    quota_zero.discount_value = discount_amount
                    quota_zero.pendiente = original_amount - discount_amount
                    self.serv_inscription_amount = original_amount - discount_amount
                    
                    # Actualizar fecha
                    self._compute_quota_zero_date(saving)
                else:
                    # Restaurar valor original si no está habilitado
                    if quota_zero.last_serv_inscription_amount > 0:
                        quota_zero.serv_inscription_amount = quota_zero.last_serv_inscription_amount
                        quota_zero.discount = 0
                        quota_zero.discount_value = 0

    def _compute_quota_zero_date(self, saving=None):
        """Calcula la fecha de la cuota 0 basada en la cuota 1"""
        if saving is None:
            for saving in self:
                self._update_quota_zero_date(saving)
        else:
            self._update_quota_zero_date(saving)

    def _update_quota_zero_date(self, saving):
        """Actualiza la fecha de la cuota 0 basada en la fecha de la cuota 1"""
        # Buscar la cuota 1 (number=1)
        quota_one = saving.line_ids.filtered(lambda l: l.number == 1)
        # quota_zero = saving.saving_line_ids.filtered(lambda l: l.number == 0)
        
        if quota_one and quota_one.date:
            date_one = quota_one.date
            
            # Calcular la fecha de la cuota 0 (un mes después de la cuota 1)
            # Ajustamos al día 20 o 21 según el mes
            if date_one.month == 7:  # Julio
                new_date = date_one + relativedelta(months=1, day=20)
            elif date_one.month == 8:  # Agosto
                new_date = date_one + relativedelta(months=1, day=21)
            else:
                # Para otros meses, usar la misma lógica: un mes después
                new_date = date_one + relativedelta(months=1)
            
            # Actualizar la fecha de la cuota 0
            quota_one.date = new_date
            quota_one.last_date = date_one
            # También actualizar last_date en account.saving
            # saving.last_date = new_date

    # @api.model_create_multi
    # def create(self, vals_list):
    #     """Sobrescribir el create para aplicar descuento al crear"""
    #     records = super(AccountSaving, self).create(vals_list)
        
    #     for record in records:
    #         # Forzar el cálculo de los campos computados
    #         record._compute_discount_values()
        
    #     return records

    # def write(self, vals):
    #     """Sobrescribir el write para manejar cambios relevantes"""
    #     result = super(AccountSaving, self).write(vals)
        
    #     # Si se cambiaron campos relevantes, recalcular
    #     if 'enable_discount' in vals or 'percent_discount' in vals or 'saving_line_ids' in vals:
    #         for record in self:
    #             record._compute_discount_values()
        
    #     return result

    # Campos computados (opcional) para mostrar información en la vista
    # discount_applied = fields.Float(
    #     string='Discount Applied',
    #     compute='_compute_discount_info',
    #     store=False
    # )
    
    # original_quota_zero_amount = fields.Float(
    #     string='Original Amount',
    #     compute='_compute_discount_info',
    #     store=False
    # )

    # @api.depends('enable_discount', 'percent_discount', 'saving_line_ids.serv_inscription_amount')
    # def _compute_discount_info(self):
    #     """Muestra información del descuento aplicado"""
    #     for saving in self:
    #         quota_zero = saving.saving_line_ids.filtered(lambda l: l.number == 0)
    #         if quota_zero and saving.enable_discount:
    #             saving.discount_applied = saving.percent_discount
    #             saving.original_quota_zero_amount = quota_zero.last_serv_inscription_amount or quota_zero.serv_inscription_amount
    #         else:
    #             saving.discount_applied = 0.0
    #             saving.original_quota_zero_amount = 0.0