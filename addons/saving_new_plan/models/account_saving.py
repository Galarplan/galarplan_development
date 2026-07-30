from odoo import _, api, fields, models
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError

class AccountSaving(models.Model):
    _inherit = 'account.saving'

    enable_discount = fields.Boolean('Habilitar')
    percent_discount = fields.Float('Descuento')
    last_date = fields.Date('new date')
    new_percent = fields.Float('Nuevo porcentaje')

    # ALEX CODE
    def action_open_discount_confirmation(self):

        return {
            'name': 'Confirmación de descuento',
            'type': 'ir.actions.act_window',
            'res_model': 'account.saving.discount.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_saving_id': self.id,
                'default_percent_discount': self.percent_discount,
            }
        }

    # END ALEX CODE

    def apply_discount_values(self):
        """Calcula los valores de descuento para la cuota 0 y actualiza fechas de otras cuotas"""
        for saving in self:
            # Procesar cuota 0 (descuento)
            self._process_quota_zero_discount(saving)
            
            # Procesar fechas de otras cuotas (excluyendo 0 y 1)
            self._update_other_quotes_dates(saving)

            # Publicar el plan únicamente si sigue en borrador
            if saving.state_plan == 'draft':
                saving.state_plan = 'posted'                    

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

            # Calcular nuevo porcentaje ALEX
            new_percent = 0.0
            if final_amount:
                new_percent = (final_amount * 100) / saving.saving_amount
            
            # Actualizar campos de la cuota 0
            quota_zero.update({
                'serv_inscription_amount': final_amount,
                'discount': saving.percent_discount,
                'discount_value': discount_amount,
                'pendiente': final_amount,
                'new_percent': new_percent,
            })
            
            # Actualizar campo en el registro principal
            saving.serv_inscription_amount = final_amount
            saving.new_percent = new_percent
            
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

            saving.new_percent = 0.0


    def _update_other_quotes_dates(self, saving):
        """Actualiza las fechas de las cuotas a partir de la cuota 0"""

        quota0 = saving.line_ids.filtered(lambda l: l.number == 0)
        if not quota0 or not quota0.date:
            return

        quota0 = quota0[0]

        # Determinar el día de pago
        if quota0.date.month == 7:
            target_day = 20
        elif quota0.date.month == 8:
            target_day = 21
        else:
            target_day = quota0.date.day

        # Fecha de la cuota 1 = un mes después de la cuota 0
        current_date = quota0.date + relativedelta(months=1)
        current_date = current_date.replace(day=target_day)

        # Actualizar cuotas 1 en adelante
        quotes = saving.line_ids.filtered(lambda l: l.number > 0).sorted('number')

        for line in quotes:
            line.date = current_date
            current_date = current_date + relativedelta(months=1)

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
        # new_date = date 
        # return new_date.replace(day=target_day)

        # ALEX
        from dateutil.relativedelta import relativedelta

        # Sumar un mes y reemplazar el día
        new_date = date + relativedelta(months=1)
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


    def facturar_with_discount(self):
        """
        Función para facturar la inscripción con descuento aplicado
        Crea una factura con el valor original y aplica el descuento como línea separada
        """
        for saving in self:
            # Obtener la línea de inscripción (número 0)
            inscription_line = saving.line_ids.filtered(lambda l: l.number == 0)
            
            if not inscription_line:
                raise ValidationError(_("No se encontró la línea de inscripción."))
            
            inscription_line = inscription_line[0]
            
            # Verificar que tenga descuento habilitado
            if not saving.enable_discount or saving.percent_discount <= 0:
                raise ValidationError(_("El plan no tiene un descuento habilitado."))
            
            # Obtener el producto de inscripción
            inscription_product = saving.saving_plan_id.inscripcion_id
            if not inscription_product:
                raise ValidationError(_("Debe configurar un producto de inscripción en el plan de ahorro."))
            
            # Valores para la factura
            original_amount = inscription_line.last_serv_inscription_amount or inscription_line.serv_inscription_amount
            discount_percent = saving.percent_discount
            discount_amount = original_amount * (discount_percent / 100)
            final_amount = original_amount - discount_amount
            
            # Crear factura
            invoice_vals = {
                'partner_id': saving.partner_id.id,
                'move_type': 'out_invoice',
                'date': fields.Date.today(),
                'invoice_date': fields.Date.today(),
                'journal_id': saving.journal_id.id,
                'company_id': saving.company_id.id,
                'currency_id': saving.currency_id.id,
                'saving_id': saving.id,
                'saving_line_id': inscription_line.id,
                'l10n_latam_document_type_id': saving.document_type_id.id,
                'l10n_ec_sri_payment_id': self.env.ref("l10n_ec.P1").id,
                'l10n_latam_use_documents': True,
                'state': 'draft',
                'is_credit_sale': saving.is_credit_sale,
                'is_credit_bank': saving.is_credit_bank,
                'is_direct': saving.is_direct,
                'is_galarplan': saving.is_galarplan,
            }
            
            # Líneas de la factura
            invoice_line_vals = []
            
            # Línea 1: Producto de inscripción con valor original
            invoice_line_vals.append((0, 0, {
                'product_id': inscription_product.id,
                'name': f"Inscripción Plan de Ahorro {saving.name}",
                'quantity': 1,
                'price_unit': original_amount,
                'tax_ids': [(6, 0, inscription_product.taxes_id.ids or [])],
            }))
            
            # Línea 2: Descuento (negativo)
            if discount_amount > 0:
                # Buscar o crear un producto para descuentos
                discount_product = self.env['product.product'].search([
                    ('name', 'ilike', 'Descuento'),
                    ('type', '=', 'service')
                ], limit=1)
                
                if not discount_product:
                    # Crear producto de descuento si no existe
                    discount_product = self.env['product.product'].create({
                        'name': 'Descuento por Pronto Pago',
                        'type': 'service',
                        'list_price': 0.0,
                        'standard_price': 0.0,
                        'taxes_id': False,
                    })
                
                invoice_line_vals.append((0, 0, {
                    'product_id': discount_product.id,
                    'name': f"Descuento {discount_percent}%",
                    'quantity': 1,
                    'price_unit': -discount_amount,  # Valor negativo para descuento
                    'tax_ids': [(6, 0, [])],  # Sin impuestos para el descuento
                }))
            
            invoice_vals['invoice_line_ids'] = invoice_line_vals
            
            # Crear y publicar la factura
            invoice = self.env['account.move'].create(invoice_vals)
            invoice.action_post()
            
            # Actualizar la línea de inscripción con el invoice_id
            inscription_line.write({
                'invoice_id': invoice.id,
                'enabled_for_invoice': False
            })
            
            # Crear registro histórico
            if 'account.saving.invoice' in self.env:
                self.env['account.saving.invoice'].create({
                    'saving_id': saving.id,
                    'invoice_ref': invoice.name,
                    'amount': invoice.amount_total,
                    'invoice_date': invoice.invoice_date,
                    'invoice_state': invoice.state,
                    'type': 'out_invoice',
                })
            
            # Devolver la acción para abrir la factura
            return {
                'type': 'ir.actions.act_window',
                'name': _('Factura de Inscripción con Descuento'),
                'res_model': 'account.move',
                'res_id': invoice.id,
                'view_mode': 'form',
                'target': 'current',
            }


    def facturar_with_discount_2(self):
        """
        Función para facturar la inscripción con descuento aplicado
        Crea una factura con el valor original y aplica el descuento como línea separada
        """
        for saving in self:
            # Obtener la línea de inscripción (número 0)
            inscription_line = saving.line_ids.filtered(lambda l: l.number == 0)
            
            if not inscription_line:
                raise ValidationError(_("No se encontró la línea de inscripción."))
            
            inscription_line = inscription_line[0]
            
            # Verificar que tenga descuento habilitado
            if not saving.enable_discount or saving.percent_discount <= 0:
                raise ValidationError(_("El plan no tiene un descuento habilitado."))
            
            # Obtener el producto de inscripción
            inscription_product = saving.saving_plan_id.inscripcion_id
            if not inscription_product:
                raise ValidationError(_("Debe configurar un producto de inscripción en el plan de ahorro."))
            
            # Valores para la factura
            original_amount = inscription_line.last_serv_inscription_amount or inscription_line.serv_inscription_amount
            discount_percent = saving.percent_discount
            discount_amount = original_amount * (discount_percent / 100)
            final_amount = original_amount - discount_amount
            
            # Crear factura
            invoice_vals = {
                'partner_id': saving.partner_id.id,
                'move_type': 'out_invoice',
                'date': fields.Date.today(),
                'invoice_date': fields.Date.today(),
                'journal_id': saving.journal_id.id,
                'company_id': saving.company_id.id,
                'currency_id': saving.currency_id.id,
                'saving_id': saving.id,
                'saving_line_id': inscription_line.id,
                'l10n_latam_document_type_id': saving.document_type_id.id,
                'l10n_ec_sri_payment_id': self.env.ref("l10n_ec.P1").id,
                'l10n_latam_use_documents': True,
                'state': 'draft',
                'is_credit_sale': saving.is_credit_sale,
                'is_credit_bank': saving.is_credit_bank,
                'is_direct': saving.is_direct,
                'is_galarplan': saving.is_galarplan,
            }
            
            # Líneas de la factura
            invoice_line_vals = []
            
            # Línea 1: Producto de inscripción con valor original y descuento aplicado directamente
            invoice_line_vals.append((0, 0, {
                'product_id': inscription_product.id,
                'name': f"Inscripción Plan de Ahorro {saving.name}",
                'quantity': 1,
                'price_unit': original_amount,
                'discount': discount_percent,  # AQUÍ SE APLICA EL DESCUENTO DIRECTAMENTE EN LA LÍNEA
                'tax_ids': [(6, 0, inscription_product.taxes_id.ids or [])],
            }))
            
            # NOTA: Ya no necesitamos la línea separada de descuento porque el campo discount
            # de la línea de factura aplica el descuento automáticamente
            
            invoice_vals['invoice_line_ids'] = invoice_line_vals
            
            # Crear y publicar la factura
            invoice = self.env['account.move'].create(invoice_vals)
            invoice.action_post()
            
            # Actualizar la línea de inscripción con el invoice_id
            inscription_line.write({
                'invoice_id': invoice.id,
                'enabled_for_invoice': False
            })
            
            # Crear registro histórico
            if 'account.saving.invoice' in self.env:
                self.env['account.saving.invoice'].create({
                    'saving_id': saving.id,
                    'invoice_ref': invoice.name,
                    'amount': invoice.amount_total,
                    'invoice_date': invoice.invoice_date,
                    'invoice_state': invoice.state,
                    'type': 'out_invoice',
                })
            
            # Devolver la acción para abrir la factura
            return {
                'type': 'ir.actions.act_window',
                'name': _('Factura de Inscripción con Descuento'),
                'res_model': 'account.move',
                'res_id': invoice.id,
                'view_mode': 'form',
                'target': 'current',
            }

    def facturar_with_discount_3(self):
        """
        Función para facturar la inscripción con descuento aplicado
        """
        for saving in self:
            # Obtener la línea de inscripción (número 0)
            inscription_line = saving.line_ids.filtered(lambda l: l.number == 0)
            
            if not inscription_line:
                raise ValidationError(_("No se encontró la línea de inscripción."))
            
            inscription_line = inscription_line[0]
            
            # Verificar que tenga descuento habilitado
            if not saving.enable_discount or saving.percent_discount <= 0:
                raise ValidationError(_("El plan no tiene un descuento habilitado."))
            
            # Obtener el producto de inscripción
            inscription_product = saving.saving_plan_id.inscripcion_id
            if not inscription_product:
                raise ValidationError(_("Debe configurar un producto de inscripción en el plan de ahorro."))
            
            # Obtener la cuenta de descuento (ID 1767 o la que corresponda)
            discount_account = self.env['account.account'].browse(1767)
            if not discount_account.exists():
                raise ValidationError(_("No se encontró la cuenta contable de descuento (ID 1767)."))
            
            # Valores para la factura
            original_amount = inscription_line.last_serv_inscription_amount or inscription_line.serv_inscription_amount
            discount_percent = saving.percent_discount
            discount_amount = original_amount * (discount_percent / 100)
            final_amount = original_amount - discount_amount
            
            # Crear factura
            invoice_vals = {
                'partner_id': saving.partner_id.id,
                'move_type': 'out_invoice',
                'date': fields.Date.today(),
                'invoice_date': fields.Date.today(),
                'journal_id': saving.journal_id.id,
                'company_id': saving.company_id.id,
                'currency_id': saving.currency_id.id,
                'saving_id': saving.id,
                'saving_line_id': inscription_line.id,
                'l10n_latam_document_type_id': saving.document_type_id.id,
                'l10n_ec_sri_payment_id': self.env.ref("l10n_ec.P1").id,
                'l10n_latam_use_documents': True,
                'state': 'draft',
                'is_credit_sale': saving.is_credit_sale,
                'is_credit_bank': saving.is_credit_bank,
                'is_direct': saving.is_direct,
                'is_galarplan': saving.is_galarplan,
            }
            
            # Líneas de la factura
            invoice_line_vals = []
            
            # Línea 1: INSCRIPCIÓN con valor ORIGINAL en el HABER
            invoice_line_vals.append((0, 0, {
                'product_id': inscription_product.id,
                'name': f"Inscripción Plan de Ahorro {saving.name}",
                'quantity': 1,
                'price_unit': original_amount,  # VALOR ORIGINAL
                'tax_ids': [(6, 0, inscription_product.taxes_id.ids or [])],
            }))
            
            # Línea 2: DESCUENTO en el DEBE (usando cuenta de descuento con valor NEGATIVO)
            if discount_amount > 0:
                invoice_line_vals.append((0, 0, {
                    'name': f"DESCUENTO EN VENTAS {discount_percent}%",
                    'quantity': 1,
                    'price_unit': -discount_amount,  # VALOR NEGATIVO para que vaya al DEBE
                    'account_id': discount_account.id,  # Cuenta de descuento
                    'tax_ids': [(6, 0, [])],
                    'product_id': False,
                }))
            
            invoice_vals['invoice_line_ids'] = invoice_line_vals
            
            # Crear la factura
            invoice = self.env['account.move'].create(invoice_vals)
            
            # Forzar que la línea de descuento tenga la cuenta correcta y sea débito
            for line in invoice.line_ids:
                if line.name and 'DESCUENTO' in line.name.upper():
                    # Asegurar que la cuenta sea la de descuento
                    line.account_id = discount_account.id
                    # Si la línea tiene balance positivo, convertir a negativo para que sea débito
                    if line.balance > 0:
                        line.price_unit = -abs(line.price_unit)
            
            # Publicar la factura
            invoice.action_post()
            
            # Actualizar la línea de inscripción con el invoice_id
            inscription_line.write({
                'invoice_id': invoice.id,
                'enabled_for_invoice': False
            })
            
            # Crear registro histórico
            if 'account.saving.invoice' in self.env:
                self.env['account.saving.invoice'].create({
                    'saving_id': saving.id,
                    'invoice_ref': invoice.name,
                    'amount': invoice.amount_total,
                    'invoice_date': invoice.invoice_date,
                    'invoice_state': invoice.state,
                    'type': 'out_invoice',
                })
            
            # Devolver la acción para abrir la factura
            return {
                'type': 'ir.actions.act_window',
                'name': _('Factura de Inscripción con Descuento'),
                'res_model': 'account.move',
                'res_id': invoice.id,
                'view_mode': 'form',
                'target': 'current',
            }