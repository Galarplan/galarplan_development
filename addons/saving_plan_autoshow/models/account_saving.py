# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

from datetime import timedelta
from odoo import fields

class AccountSaving(models.Model):
    _inherit = 'account.saving'

    quotes_ids = fields.One2many('account.saving.quotes','saving_id')

    number_quotas = fields.Integer('# cuotas premium',default=0)

    premiun_quote = fields.Float('Cuota premium',default=0.0,compute='_compute_data_autoshow')

    quote_per_number = fields.Float('cuota/numero',default=0.0,compute='_compute_data_autoshow')

    premiun_quote_pending = fields.Float('Cuota Premiun Pendiente',compute='_compute_premiun_quote',default=0.0)

    premiun_quote_paid = fields.Float('Cuota Premium Pagada',compute='_compute_premiun_quote',default=0.0)

    special_quote_number = fields.Integer('Cuota Especial')

    # CODE ALEX
    @api.onchange('special_quote_number', 'saving_plan_id')
    def _onchange_special_quote_number(self):
        for record in self:
            if not record.special_quote_number or not record.saving_plan_id:
                continue

            saving_amount = record.saving_plan_id.saving_amount
            percent_big_quote = record.saving_plan_id.percent_big_quote

            if 12000 <= saving_amount <= 30000 and percent_big_quote == 30:
                if record.special_quote_number not in [10, 11, 12]:
                    record.special_quote_number = False

                    return {
                        'warning': {
                            'title': 'Validación Cuota Flex',
                            'message': (
                                'El número de cuota especial no es válido.\n\n'
                                'Para planes con un monto de ahorro entre '
                                '$12.000 y $30.000 y un porcentaje de cuota '
                                'las cuotas 10, 11 o 12.'
                            ),
                        }
                    }
                
            # Entre $12.000 y $30.000 con 35%
            if 12000 <= saving_amount <= 30000 and percent_big_quote == 35:
                if record.special_quote_number not in [7, 8, 9]:
                    record.special_quote_number = False

                    return {
                        'warning': {
                            'title': 'Validación Cuota Flex',
                            'message': (
                                'El número de cuota especial no es válido.\n\n'
                                'Para planes con un monto de ahorro entre '
                                '$12.000 y $30.000 y un porcentaje de cuota '
                                'especial del 35%, solamente puede utilizar '
                                'las cuotas 7, 8 o 9.'
                            ),
                        }
                    }  

            # Entre $12.000 y $30.000 con 20%
            if 12000 <= saving_amount <= 30000 and percent_big_quote == 20:
                if record.special_quote_number not in [16, 17, 18]:
                    record.special_quote_number = False

                    return {
                        'warning': {
                            'title': 'Validación Cuota Flex',
                            'message': (
                                'El número de cuota especial no es válido.\n\n'
                                'Para planes con un monto de ahorro entre '
                                '$12.000 y $30.000 y un porcentaje de cuota '
                                'especial del 20%, solamente puede utilizar '
                                'las cuotas 16, 17 o 18.'
                            ),
                        }
                    }

            # Entre $12.000 y $30.000 con 25%
            if 12000 <= saving_amount <= 30000 and percent_big_quote == 25:
                if record.special_quote_number not in [13, 14, 15]:
                    record.special_quote_number = False

                    return {
                        'warning': {
                            'title': 'Validación Cuota Flex',
                            'message': (
                                'El número de cuota especial no es válido.\n\n'
                                'Para planes con un monto de ahorro entre '
                                '$12.000 y $30.000 y un porcentaje de cuota '
                                'especial del 25%, solamente puede utilizar '
                                'las cuotas 13, 14 o 15.'
                            ),
                        }
                    }
                                              
    # FIN CODE ALEX

    @api.depends('saving_plan_id','number_quotas')
    def _compute_data_autoshow(self):
        for record in self:
            record.premiun_quote = (record.saving_plan_id.percent_big_quote/100) * record.saving_amount
            if record.number_quotas>0:
                record.quote_per_number = round(record.premiun_quote/record.number_quotas,2)
            else:
                record.quote_per_number = record.premiun_quote

    @api.depends('quotes_ids','quotes_ids.paid_value','quotes_ids.pending_value')
    def _compute_premiun_quote(self):
        for record in self:
            premiun_quote_pending = 0.0
            premiun_quote_paid = 0.0
            
            # Calculate totals from related quotes
            for quote in record.quotes_ids:
                premiun_quote_pending += quote.pending_value
                premiun_quote_paid += quote.paid_value
            
            record.premiun_quote_pending = premiun_quote_pending
            record.premiun_quote_paid = premiun_quote_paid



    def compute_quotes_lines(self):
        from decimal import Decimal, ROUND_HALF_UP
                    
        def round_excel(value):
            return float(Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

        
        for brw_each in self:
            brw_each.quotes_ids.unlink()
            brw_each.line_ids.unlink()
            # Calcular el total de la cuota premiun
            total_premiun = round_excel(brw_each.saving_amount * (brw_each.saving_plan_id.percent_big_quote / 100))
            # Acumular los valores de quotes
            quotes_vals_list = []


            
            # Calcular el valor por cada cuota premiun
            if brw_each.number_quotas > 0:
                quote_per_number = round_excel(total_premiun / brw_each.number_quotas)
                for i in range(brw_each.number_quotas):
                    datevalue = brw_each.start_date + relativedelta(months=i + 1)
                    quote_vals = {
                        'saving_id': brw_each.id,
                        'number': i + 1,
                        'value': quote_per_number,
                        'paid_value': 0.00,
                        'pending_value': quote_per_number,
                    }
                    quotes_vals_list.append((0, 0, quote_vals))
            else:
                quote_per_number = total_premiun
                quote_vals = {
                    'saving_id': brw_each.id,
                    'number': 1,
                    'value': quote_per_number,
                    'paid_value': 0.00,
                    'pending_value': quote_per_number,
                }
                quotes_vals_list.append((0, 0, quote_vals))
            brw_each.quotes_ids = quotes_vals_list
        

    def compute_inscription_lines(self):

        from decimal import Decimal, ROUND_HALF_UP
                    
        def round_excel(value):
            return float(Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

        for brw_each in self:
            new_date_process = brw_each.start_date
            total = 0.00
            totalglobal = 0.00
            principal_amount = brw_each.periods!=0 and round_excel(brw_each.saving_amount/brw_each.periods) or 0.00
            line_ids = [(5,)]
            ###inscripcion
            # print('===================',brw_each.rate_inscription_plan,round_excel(brw_each.saving_amount * brw_each.rate_inscription_plan / 100.00))
            values = {
                "sequence": 0,
                "number": 0,
                "date": brw_each.start_date,
                "pagos": 0.00,
                "pendiente": 0.00,
                "estado_pago": "sin_aplicar",
                "parent_saving_state": "draft",
                "enabled_for_invoice": False,
                "migrated": False,
                "migrated_has_invoices": False,
                "migrated_payment_amount": False,
                # "serv_inscription_amount": round_excel(brw_each.saving_amount * brw_each.saving_plan_id.rate_inscription / 100.00),
                "serv_inscription_amount": round_excel(brw_each.saving_amount * brw_each.rate_inscription_plan / 100.00),
                # "rate_inscription": brw_each.saving_plan_id.rate_inscription,
                "rate_inscription": brw_each.rate_inscription_plan,

            }
            line_ids.append((0, 0, values))
            ####
            
            brw_each.line_ids= line_ids
            #brw_each.compute_inscription()



    def compute_lines_premiun(self):

        from decimal import Decimal, ROUND_HALF_UP
                            
        def round_excel(value):
            return float(Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

        self.compute_quotes_lines()

        self.compute_inscription_lines()

        for brw_each in self:
            existing_lines = brw_each.line_ids.ids
        
            # Si hay líneas existentes, las mantenemos
            if existing_lines:
                # Crear comando para mantener líneas existentes
                line_ids = [(6, 0, existing_lines)]
            else:
                line_ids = []

            admin_values = round_excel(brw_each.saving_amount * ((brw_each.saving_plan_id.rate_expense/100)*(brw_each.saving_plan_id.periods/12)))
            financial = round_excel(brw_each.saving_amount - brw_each.premiun_quote + admin_values)
            gl_mensual = round_excel((brw_each.saving_plan_id.gl_legal*1.3)/brw_each.periods)
            disp_mensual = round_excel((brw_each.saving_plan_id.device_value*1.3)/brw_each.periods)
            principal_amount = brw_each.periods!=0 and round_excel(brw_each.saving_amount/brw_each.periods) or 0.00
            valor_fijo_seguro=round_excel(principal_amount * brw_each.saving_plan_id.rate_insurance / 100.00)
            serv_admin_fijo=round_excel(principal_amount * brw_each.saving_plan_id.rate_expense / 100.00)
            total_decremento=0
            total = 0.00
            totalglobal = 0.00
            #line_ids = [(5,)]
            
            for each_range in range(0, brw_each.periods):
                quota = each_range +1
                new_date_process_temp = brw_each.start_date + relativedelta(months=brw_each.number_quotas + each_range + 1)
                anios=brw_each.periods/12
                datevalue =new_date_process_temp
                #principal_amount= brw_each.fixed_amount
                total += round_excel(principal_amount)
                decremento_seguro=anios!=0 and (valor_fijo_seguro/anios) or 0
                if brw_each.periods == quota :#en la ultima se hace el ajuste
                    principal_amount = round_excel(principal_amount + round_excel((brw_each.saving_amount - total)))
                serv_admin=serv_admin_fijo
                if valor_fijo_seguro>0.00:
                    #mult_cuota=1
                    if each_range % 12 == 0 and each_range != 0:
                        valor_fijo_seguro = round_excel(valor_fijo_seguro - decremento_seguro)
                        total_decremento+=decremento_seguro
                    serv_admin+=round_excel(total_decremento)
                saving_amount_temp = round_excel(brw_each.fixed_amount + serv_admin + valor_fijo_seguro)
                dif=brw_each.quota_amount-saving_amount_temp
                if dif!=0.00:
                    serv_admin=round_excel(serv_admin+dif)
                #saving_amount = min_saving_amount
                #print('=============================',brw_each.quota_amount,brw_each.fixed_amount,1+(brw_each.saving_plan_id.iva_amount_percent/100),(brw_each.quota_amount - brw_each.fixed_amount)*(1+(brw_each.saving_plan_id.iva_amount_percent/100)))
                values = {
                    "sequence":each_range ,
                    "number":quota,
                    "date":datevalue,
                    "pagos":0.00,
                    "pendiente":0.00,
                    "estado_pago":"sin_aplicar",
                    "parent_saving_state":"draft",
                    "enabled_for_invoice":False,
                    "migrated":False,
                    "migrated_has_invoices":False,
                    "migrated_payment_amount":False,
                    "saving_amount": brw_each.quota_amount + gl_mensual + disp_mensual if brw_each.saving_plan_id.with_aditions else brw_each.quota_amount ,
                    "principal_amount":brw_each.saving_plan_id.fixed_amount,
                    #"serv_admin_amount":serv_admin ,
                    "serv_admin_amount": (brw_each.quota_amount - brw_each.fixed_amount),
                    "seguro_amount": valor_fijo_seguro,
                    "serv_admin_percentage":  brw_each.saving_plan_id.rate_expense,
                    "seguro_percentage": brw_each.saving_plan_id.rate_insurance,
                    "gl_mensual": gl_mensual,
                    "disp_mensual": disp_mensual
                }
                # print(values)
                line_ids.append((0, 0, values))
                totalglobal += round_excel(principal_amount)
                if totalglobal > brw_each.saving_amount:
                    continue
            brw_each.line_ids= line_ids


    
    def compute_lines_flex(self):
        from decimal import Decimal, ROUND_HALF_UP
                                    
        def round_excel(value):
            return float(Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

        #self.compute_quotes_lines()

        self.compute_inscription_lines()

        for brw_each in self:
            existing_lines = brw_each.line_ids.ids
        
            # Si hay líneas existentes, las mantenemos
            if existing_lines:
                # Crear comando para mantener líneas existentes
                line_ids = [(6, 0, existing_lines)]
            else:
                line_ids = []

            admin_values = round_excel(brw_each.saving_amount * ((brw_each.saving_plan_id.rate_expense/100)*(brw_each.saving_plan_id.periods/12)))
            financial = round_excel(brw_each.saving_amount - brw_each.premiun_quote + admin_values)
            gl_mensual = round_excel((brw_each.saving_plan_id.gl_legal*1.3)/brw_each.periods)
            disp_mensual = round_excel((brw_each.saving_plan_id.device_value*1.3)/brw_each.periods)
            principal_amount = brw_each.periods!=0 and round_excel(brw_each.saving_amount/brw_each.periods) or 0.00
            valor_fijo_seguro=round_excel(principal_amount * brw_each.saving_plan_id.rate_insurance / 100.00)
            serv_admin_fijo=round_excel(principal_amount * brw_each.saving_plan_id.rate_expense / 100.00)
            total_decremento=0
            total = 0.00
            totalglobal = 0.00
            #line_ids = [(5,)]
            
            for each_range in range(0, brw_each.periods):
                quota = each_range +1
                new_date_process_temp = brw_each.start_date + relativedelta(months=brw_each.number_quotas + each_range + 1)
                anios=brw_each.periods/12
                datevalue =new_date_process_temp
                #principal_amount= brw_each.fixed_amount
                total += round_excel(principal_amount)
                decremento_seguro=anios!=0 and (valor_fijo_seguro/anios) or 0
                if brw_each.periods == quota :#en la ultima se hace el ajuste
                    principal_amount = round_excel(principal_amount + round_excel((brw_each.saving_amount - total)))
                serv_admin=serv_admin_fijo
                if valor_fijo_seguro>0.00:
                    #mult_cuota=1
                    if each_range % 12 == 0 and each_range != 0:
                        valor_fijo_seguro = round_excel(valor_fijo_seguro - decremento_seguro)
                        total_decremento+=decremento_seguro
                    serv_admin+=round_excel(total_decremento)
                saving_amount_temp = round_excel(brw_each.fixed_amount + serv_admin + valor_fijo_seguro)
                dif=brw_each.quota_amount-saving_amount_temp
                if dif!=0.00:
                    serv_admin=round_excel(serv_admin+dif)
                #saving_amount = min_saving_amount
                #print('=============================',brw_each.quota_amount,brw_each.fixed_amount,1+(brw_each.saving_plan_id.iva_amount_percent/100),(brw_each.quota_amount - brw_each.fixed_amount)*(1+(brw_each.saving_plan_id.iva_amount_percent/100)))
                if brw_each.special_quote_number == quota:
                    values = {
                        "sequence":each_range ,
                        "number":quota,
                        "date":datevalue,
                        "pagos":0.00,
                        "pendiente":0.00,
                        "estado_pago":"sin_aplicar",
                        "parent_saving_state":"draft",
                        "enabled_for_invoice":False,
                        "migrated":False,
                        "migrated_has_invoices":False,
                        "migrated_payment_amount":False,
                        "saving_amount": brw_each.premiun_quote ,
                        "principal_amount":brw_each.premiun_quote,
                        #"serv_admin_amount":serv_admin ,
                        "serv_admin_amount": (brw_each.quota_amount - brw_each.fixed_amount),
                        "seguro_amount": valor_fijo_seguro,
                        "serv_admin_percentage":  brw_each.saving_plan_id.rate_expense,
                        "seguro_percentage": brw_each.saving_plan_id.rate_insurance,
                        "gl_mensual": gl_mensual,
                        "disp_mensual": disp_mensual
                    }
                else:
                    values = {
                        "sequence":each_range ,
                        "number":quota,
                        "date":datevalue,
                        "pagos":0.00,
                        "pendiente":0.00,
                        "estado_pago":"sin_aplicar",
                        "parent_saving_state":"draft",
                        "enabled_for_invoice":False,
                        "migrated":False,
                        "migrated_has_invoices":False,
                        "migrated_payment_amount":False,
                        "saving_amount": brw_each.quota_amount + gl_mensual + disp_mensual if brw_each.saving_plan_id.with_aditions else brw_each.quota_amount ,
                        "principal_amount":brw_each.saving_plan_id.fixed_amount,
                        #"serv_admin_amount":serv_admin ,
                        "serv_admin_amount": (brw_each.quota_amount - brw_each.fixed_amount),
                        "seguro_amount": valor_fijo_seguro,
                        "serv_admin_percentage":  brw_each.saving_plan_id.rate_expense,
                        "seguro_percentage": brw_each.saving_plan_id.rate_insurance,
                        "gl_mensual": gl_mensual,
                        "disp_mensual": disp_mensual
                    }
                    
                # print(values)
                line_ids.append((0, 0, values))
                totalglobal += round_excel(principal_amount)
                if totalglobal > brw_each.saving_amount:
                    continue
            brw_each.line_ids= line_ids


    def compute_lines_normal(self):
            from decimal import Decimal, ROUND_HALF_UP
    
            def round_excel(value):
                return float(Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    
            for brw_each in self:
                new_date_process = brw_each.start_date
                total = 0.00
                totalglobal = 0.00
                principal_amount = brw_each.periods!=0 and round_excel(brw_each.saving_amount/brw_each.periods) or 0.00
                line_ids = [(5,)]
                ###inscripcion
                # print('===================',brw_each.rate_inscription_plan,round_excel(brw_each.saving_amount * brw_each.rate_inscription_plan / 100.00))
                values = {
                    "sequence": 0,
                    "number": 0,
                    "date": brw_each.start_date,
                    "pagos": 0.00,
                    "pendiente": 0.00,
                    "estado_pago": "sin_aplicar",
                    "parent_saving_state": "draft",
                    "enabled_for_invoice": False,
                    "migrated": False,
                    "migrated_has_invoices": False,
                    "migrated_payment_amount": False,
                    # "serv_inscription_amount": round_excel(brw_each.saving_amount * brw_each.saving_plan_id.rate_inscription / 100.00),
                    "serv_inscription_amount": round_excel(brw_each.saving_amount * brw_each.rate_inscription_plan / 100.00),
                    # "rate_inscription": brw_each.saving_plan_id.rate_inscription,
                    "rate_inscription": brw_each.rate_inscription_plan,
    
                }
                line_ids.append((0, 0, values))
                ####
                valor_fijo_seguro=round_excel(principal_amount * brw_each.saving_plan_id.rate_insurance / 100.00)
                anios=brw_each.periods/12
                decremento_seguro=anios!=0 and (valor_fijo_seguro/anios) or 0
                total_decremento=0
                serv_admin_fijo=round_excel(principal_amount * brw_each.saving_plan_id.rate_expense / 100.00)
                min_saving_amount=0.00
                for each_range in range(0, brw_each.periods):
                    # print( brw_each.periods)
                    quota = each_range +1
                    new_date_process_temp =brw_each.start_date+ relativedelta(months=each_range)
                    datevalue =new_date_process_temp
                    total += round_excel(principal_amount)
                    principal_amount= brw_each.fixed_amount
                    if brw_each.periods == quota :#en la ultima se hace el ajuste
                        principal_amount = round_excel(principal_amount + round_excel((brw_each.saving_amount - total)))
                    serv_admin=serv_admin_fijo
                    if valor_fijo_seguro>0.00:
                        #mult_cuota=1
                        if each_range % 12 == 0 and each_range != 0:
                            valor_fijo_seguro = round_excel(valor_fijo_seguro - decremento_seguro)
                            total_decremento+=decremento_seguro
                        serv_admin+=round_excel(total_decremento)
                    saving_amount_temp = round_excel(brw_each.fixed_amount + serv_admin + valor_fijo_seguro)
                    dif=brw_each.quota_amount-saving_amount_temp
                    if dif!=0.00:
                        serv_admin=round_excel(serv_admin+dif)
                    #saving_amount = min_saving_amount
                    values = {
                        "sequence":each_range ,
                        "number":quota,
                        "date":datevalue,
                        "pagos":0.00,
                        "pendiente":0.00,
                        "estado_pago":"sin_aplicar",
                        "parent_saving_state":"draft",
                        "enabled_for_invoice":False,
                        "migrated":False,
                        "migrated_has_invoices":False,
                        "migrated_payment_amount":False,
                       "saving_amount": brw_each.quota_amount,
                        "principal_amount":principal_amount,
                        "serv_admin_amount":serv_admin ,
                       "seguro_amount": valor_fijo_seguro,
                       "serv_admin_percentage":  brw_each.saving_plan_id.rate_expense,
                       "seguro_percentage": brw_each.saving_plan_id.rate_insurance
                    }
                    # print(values)
                    line_ids.append((0, 0, values))
                    totalglobal += round_excel(principal_amount)
                    if totalglobal > brw_each.saving_amount:
                        continue
                brw_each.line_ids= line_ids
                brw_each.compute_inscription()


    def compute_lines(self):
        for record in self:
            if record.saving_type == 'premiun':
                self.compute_lines_premiun()
            elif record.saving_type == 'flex':
                self.compute_lines_flex()
            else:
                self.compute_lines_normal()
