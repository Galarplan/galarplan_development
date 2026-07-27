from odoo import _, api, fields, models
from dateutil.relativedelta import relativedelta

class AccountSaving(models.Model):
    _inherit = 'account.saving'

    enable_discount = fields.Boolean('Habilitar')
    percent_discount = fields.Float('Descuento')
    last_date = fields.Date('new date')


    def apply_discount_values(self):
        """Calcula los valores de descuento para la cuota 0 y actualiza fechas de otras cuotas"""
        for saving in self:
            # Procesar cuota 0 (descuento)
            self._process_quota_zero_discount(saving)
            
            # Procesar fechas de otras cuotas (excluyendo 0 y 1)
            self._update_other_quotes_dates(saving)

    def _process_quota_zero_discount(self, saving):
        """Procesa el descuento de la cuota 0"""
        quota_zero = saving.line_ids.filtered(lambda l: l.number == 0)
        
        if not quota_zero:
            return
        
        if saving.enable_discount and saving.percent_discount > 0:
            # Aplicar descuento
            original_amount = quota_zero.serv_inscription_amount
            
            # Guardar valor original solo si no existe
            if quota_zero.last_serv_inscription_amount == 0:
                quota_zero.last_serv_inscription_amount = original_amount
            
            # Calcular y aplicar descuento
            discount_amount = original_amount * (saving.percent_discount / 100)
            final_amount = original_amount - discount_amount
            
            # Actualizar campos de la cuota 0
            quota_zero.update({
                'serv_inscription_amount': final_amount,
                'discount': saving.percent_discount,
                'discount_value': discount_amount,
                'pendiente': final_amount,
            })
            
            # Actualizar campo en el registro principal
            saving.serv_inscription_amount = final_amount
            
            # Actualizar fecha de cuota 0 basada en cuota 1
            self._update_quota_zero_date(saving)
            
        else:
            # Restaurar valor original si el descuento está deshabilitado
            if quota_zero.last_serv_inscription_amount > 0:
                quota_zero.update({
                    'serv_inscription_amount': quota_zero.last_serv_inscription_amount,
                    'discount': 0,
                    'discount_value': 0,
                })

    def _update_other_quotes_dates(self, saving):
        """Actualiza las fechas de las cuotas excluyendo 0 y 1"""
        other_quotes = saving.line_ids.filtered(lambda l: l.number not in [0,1])
        
        for line in other_quotes:
            if not line.date:
                continue
                
            new_date = self._calculate_new_date(line.date, saving)
            line.date = new_date

        # Actualizar también la fecha de fin
        if saving.end_date:
            new_end_date = self._calculate_new_date(saving.end_date, saving)
            saving.end_date = new_end_date

    def _calculate_new_date(self, date, saving):
        """Solo reemplaza el día según el mes de inicio del plan"""
        # Obtener el mes de inicio
        start_month = saving.start_date.month if saving.start_date else date.month
        
        # Determinar el día objetivo
        if start_month == 7:
            target_day = 20
        elif start_month == 8:
            target_day = 21
        else:
            # Si no es julio ni agosto, mantener el mismo día
            return date
        
        # Sumar un mes y reemplazar solo el día
        new_date = date 
        return new_date.replace(day=target_day)





        
        

    def _update_quota_zero_date(self, saving):
        """Actualiza la fecha de la cuota 0 basada en la cuota 1"""
        quota_one = saving.line_ids.filtered(lambda l: l.number == 1)
        
        if quota_one and quota_one.date:
            new_date = self._calculate_new_date(quota_one.date,saving)
            quota_one.date = new_date
            quota_one.last_date = quota_one.date  # Guardar fecha anterior si es necesario

    def _get_quota_lines_by_number(self, saving, number):
        """Obtiene líneas de cuota por número (helper method)"""
        return saving.line_ids.filtered(lambda l: l.number == number)