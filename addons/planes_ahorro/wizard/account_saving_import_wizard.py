# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api,fields, models,_
from xlrd import open_workbook
from odoo.exceptions import ValidationError
from ...calendar_days.tools import CalendarManager,DateManager
from ...message_dialog.tools import FileManager
dtObj=DateManager()
clObj=CalendarManager()
flObj=FileManager()
import datetime
from datetime import datetime, timedelta

class AccountSavingImportWizard(models.TransientModel):
    _name="account.saving.import.wizard"
    _description="Asistente de Movimientos Diferidos del Empleado"
    
    @api.model
    def get_default_saving_id(self):
        return self._context.get("active_ids",False) and self._context["active_ids"][0] or False
    
    @api.model
    def get_default_company_id(self):
        if self._context.get("active_ids",False):
            for brw_each in self.env["account.saving"].sudo().browse(self._context["active_ids"]):
                return brw_each.company_id.id
        return False

    @api.model
    def get_default_partner_id(self):
        if self._context.get("active_ids", False):
            for brw_each in self.env["account.saving"].sudo().browse(self._context["active_ids"]):
                return brw_each.partner_id.id
        return False

    saving_id=fields.Many2one("account.saving", "Plan de Ahorro",required=False,default=get_default_saving_id)
    company_id=fields.Many2one("res.company",string="Compañia",required=False,default=get_default_company_id)
    partner_id = fields.Many2one("res.partner", string="Cliente", required=False, default=get_default_partner_id)

    currency_id = fields.Many2one("res.currency", "Moneda", related="company_id.currency_id", store=False,
                                  readonly=True)
    file=fields.Binary("Archivo",required=False,filters='*.xlsx')
    file_name=fields.Char("Nombre de Archivo",required=False,size=255)
    type=fields.Selection([('file','Archivo'),
                           ('assign','Asignar')
                           ],string="Tipo",default="file")
    line_ids=fields.One2many('account.saving.import.line.wizard','wizard_id','Detalle')

    @api.onchange('saving_id','type')
    def onchange_type(self):
        print(1)
        if self.type!='file':
            line_ids=[(5,)]
            historic_invoice_ids={}
            for brw_invoice_migrated in self.saving_id.historic_invoice_ids:
                if brw_invoice_migrated.invoice_state=='posted':
                    historic_invoice_ids[brw_invoice_migrated.saving_line_id]=brw_invoice_migrated.invoice_ref
            for brw_line in self.saving_id.line_ids:
                print(brw_line)
                brw_invoice=self.get_invoice(brw_line,historic_invoice_ids)
                line_ids.append((0,0,{
                    "line_id":brw_line.id,
                    "total":brw_line.saving_amount+brw_line.serv_inscription_amount,
                    "invoice_id":brw_line and brw_line.invoice_id.id or brw_invoice,
                    "name":brw_line and brw_line.invoice_id.name or (brw_invoice and brw_invoice.name or '')
                }))
            print(2)
            self.line_ids=line_ids

    def get_invoice(self,brw_line,historic_invoice_ids):
        brw_invoice=None
        if brw_line in historic_invoice_ids:
            self._cr.execute(f"""select am.id, am.ref 
    from account_move am 
    inner join account_move_line aml on aml.move_id=am.id
    
    where aml.partner_id={brw_line.saving_id.partner_id.id} and am.ref ilike '%{historic_invoice_ids[brw_line]}%'
    group by am.id, am.ref """)
            result=self._cr.fetchone()
            if result:
                brw_invoice=self.env["account.move"].sudo().browse(result[0])
        return brw_invoice

    def process(self):
        for brw_each in self:
            if brw_each.type=='file':
               brw_each.process_file()
            else:
                brw_each.process_assign()
        return True

    def process_file(self):

        def clean_value(value, default=0.0, is_int=False):
            """Convierte valores del Excel a float/int y maneja separadores de miles y decimales."""
            if value is None or value == "":
                return int(default) if is_int else default
            value = str(value).replace(",", ".")  # Reemplaza coma por punto si es necesario
            try:
                return int(float(value)) if is_int else float(value)
            except ValueError:
                return int(default) if is_int else default


        def excel_date_to_date(excel_date):
            # Excel date starts from January 1, 1900, but has an off-by-one bug (1900 is treated as a leap year).
            # To fix this, subtract 2 days.
            base_date = datetime(1900, 1, 1) - timedelta(days=2)

            # Convert the Excel date (integer or float) to a date
            if isinstance(excel_date, float) or isinstance(excel_date, int):
                return base_date + timedelta(days=int(excel_date))
            return None

        NUMERO = 0
        FECHA = 1
        PLANES_DE_AHORRO = 3
        APORTACION = 2
        SERVICIO_ADMINISTRATIVO = 4
        SEGURO = 5
        INSCRIPCION = 6
        PORCENTAJE_SERVICIO_ADMINISTRATIVO = 7
        PORCENTAJE_SEGURO = 8
        PORCENTAJE_INSCRIPCION = 9
        DEC=2
        for brw_each in self:
            line_ids = [(5,)]
            ext=flObj.get_ext(brw_each.file_name)
            fileName=flObj.create(ext)
            flObj.write(fileName,flObj.decode64((brw_each.file)))
            book = open_workbook(fileName)
            sheet = book.sheet_by_index(0)
            for row_index in range(0, sheet.nrows):
                if row_index==0:
                    continue
                # Leer valores del Excel
                numero = str(sheet.cell(row_index, NUMERO).value).replace('.0', '') or "SIN NUMERO"
                fecha = sheet.cell(row_index, FECHA).value
                planes_ahorro = clean_value(sheet.cell(row_index, PLANES_DE_AHORRO).value)

                aportacion = clean_value(sheet.cell(row_index, APORTACION).value)
                servicio_administrativo = clean_value(sheet.cell(row_index, SERVICIO_ADMINISTRATIVO).value)
                seguro = clean_value(sheet.cell(row_index, SEGURO).value)
                inscripcion = clean_value(sheet.cell(row_index, INSCRIPCION).value)
                porcentaje_servicio_administrativo = clean_value(
                    sheet.cell(row_index, PORCENTAJE_SERVICIO_ADMINISTRATIVO).value)
                porcentaje_seguro = clean_value(sheet.cell(row_index, PORCENTAJE_SEGURO).value)
                porcentaje_inscripcion = clean_value(sheet.cell(row_index, PORCENTAJE_INSCRIPCION).value)

                # Validación: al menos un valor debe ser mayor a 0
                if not any([aportacion, planes_ahorro, servicio_administrativo, seguro, inscripcion]):
                    raise ValueError(
                        f"Error en la fila {row_index}: Al menos un valor entre APORTACION, PLANES DE AHORRO, SERVICIO ADMINISTRATIVO, SEGURO e INSCRIPCION debe ser mayor a 0.")
                numero=int(numero)
                fecha=excel_date_to_date(fecha)
                if numero == 0:
                    if inscripcion>0.00:
                        values = {
                            "sequence": 0,
                            "number": 0,
                            "date": fecha,
                            "pagos": 0.00,
                            "pendiente": 0.00,
                            "estado_pago": "sin_aplicar",
                            "parent_saving_state": "draft",
                            "enabled_for_invoice": False,
                            "migrated": False,
                            "migrated_has_invoices": False,
                            "migrated_payment_amount": False,
                            "serv_inscription_amount": inscripcion,
                            "rate_inscription": porcentaje_inscripcion,
                        }
                        line_ids.append((0, 0, values))
                else:
                    total=planes_ahorro +servicio_administrativo+seguro
                    if round(aportacion ,DEC)!=round(total,DEC):
                        raise ValidationError(_("El valor de la aportacion deberia ser la suma de planes de ahorro,serv. administrativo y seguro"))
                    values = {
                        "sequence": numero,
                        "number": numero+1,
                        "date": fecha,
                        "pagos": 0.00,
                        "pendiente": 0.00,
                        "estado_pago": "sin_aplicar",
                        "parent_saving_state": "draft",
                        "enabled_for_invoice": False,
                        "migrated": False,
                        "migrated_has_invoices": False,
                        "migrated_payment_amount": False,
                        "principal_amount":planes_ahorro    ,
                        "saving_amount": aportacion,
                        "serv_admin_amount": servicio_administrativo,
                        "seguro_amount": seguro,
                        "serv_admin_percentage": porcentaje_servicio_administrativo,
                        "seguro_percentage": porcentaje_seguro,
                    }
                    line_ids.append((0, 0, values))
            brw_each.saving_id.write({"line_ids":line_ids})
        return True

    def process_assign(self):
        for brw_each in self:
            for brw_line in brw_each.line_ids:
                brw_line.line_id.write({"invoice_id":brw_line.invoice_id and brw_line.invoice_id.id or False})
        return True

class AccountSavingImportLineWizard(models.TransientModel):
    _name="account.saving.import.line.wizard"

    wizard_id=fields.Many2one("account.saving.import.wizard",ondelete="cascade")
    line_id=fields.Many2one('account.saving.lines',"Cuota",required=True)
    invoice_id = fields.Many2one('account.move', "Factura", required=False)
    name=fields.Char("# Documento")
    total=fields.Float("Total")
    ref=fields.Char(related="invoice_id.ref",store=False,readonly=True)
