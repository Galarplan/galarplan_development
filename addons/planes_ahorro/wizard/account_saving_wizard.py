# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api,fields, models,_
from xlrd import open_workbook
from odoo.exceptions import ValidationError
import os
import tempfile
import xlsxwriter
import xlrd
from datetime import datetime, timedelta

status_dict_inverted = {
    'Borrador': 'draft',
    'Publicado': 'posted',
    'Activo': 'active',
    'Adjudicado con Bien': 'adjudicated_with_assets',
    'Adjudicado sin Bien': 'adjudicated_without_assets',
    'Adjudicado': 'awarded',
    'Autorización de Retiro Pendiente': 'pending_authorizated',
    'Anulado': 'anulled',
    'Desactivado': 'disabled',
    'Retirado': 'retired',
    'Cancelado': 'cancelled',
    'Cerrado': 'closed',
}

class AccountSavingWizard(models.Model):
    _name="account.saving.wizard"
    _description="Asistente para Importar Planes de Ahorro"

    company_id = fields.Many2one(
        "res.company",
        string="Compañia",
        required=True,
        copy=False,
        default=lambda self: self.env.company,
    )
    
    file=fields.Binary("Archivo",required=False,filters='*.xlsx')
    file_name=fields.Char("Nombre de Archivo",required=False,size=255)

    file_payment = fields.Binary("Archivo", required=False, filters='*.xlsx')
    file_payment_name = fields.Char("Nombre de Archivo", required=False, size=255)

    file_result = fields.Binary("Archivo Resultado", required=False, filters='*.xlsx')
    file_name_result = fields.Char("Nombre de Archivo Resultado", required=False, size=255)

    file_payment_result = fields.Binary("Archivo Resultado Pagos", required=False, filters='*.xlsx')
    file_payment_name_result = fields.Char("Nombre de Archivo Resultado Pagos", required=False, size=255)

    _rec_name="id"
    _order="id desc"

    def process(self):
        for brw_each in self:
            brw_each.process_file()
        return True

    import os

    def get_ext(self,file_name):
        return os.path.splitext(file_name)[1][1:]



    def create_file(self,ext):
        # Asegurar que la extensión comienza con un punto
        ext = f".{ext.lstrip('.')}"

        # Crear un archivo temporal con la extensión deseada
        temp_file = tempfile.NamedTemporaryFile(suffix=ext, delete=False)

        # Retornar la ruta del archivo temporal
        return temp_file.name

    def write_file(self,filename,str_data,modeWrite="wb"):
        import base64
        with open(filename, mode=modeWrite) as file:
            file.write(base64.b64decode(str_data)   )
        return str_data

    def guardar_mensajes(self, mensajes):
        import base64
        """ Guarda los errores en un archivo Excel y retorna el contenido en binario """
        if not mensajes:
            return None  # Si no hay errores, no retorna nada
        import io
        output = io.BytesIO()  # Crea un buffer en memoria
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()
        print(mensajes)
        # Escribir encabezados
        worksheet.write(0, 0, "id")
        worksheet.write(0, 1, "Nombre")
        worksheet.write(0, 2, "Valores")
        worksheet.write(0, 3, "Mensaje")

        # Escribir errores en las filas
        for row_idx, (id,nombre,valores, mensaje) in enumerate(mensajes, start=1):
            worksheet.write(row_idx, 0, id)
            worksheet.write(row_idx, 1, nombre)
            worksheet.write(row_idx, 2, str(valores))
            worksheet.write(row_idx, 3, mensaje)

        workbook.close()

        output.seek(0)  # Mover el cursor al inicio del buffer antes de retornarlo
        return base64.b64encode(output.read())

    def ejecutar_transaccion(self, nombre, values,procesados, mensajes):
        """ Ejecuta la transacción y guarda mensajes si los hay """
        OBJ_PLAN = self.env["account.saving"].sudo()
        #print(values)
        srch_plan = OBJ_PLAN.search([('name', '=', nombre),
                                     ('partner_id','=',values["partner_id"]),
                                      ('start_date','=',values["start_date"].date()),
                                      ('saving_plan_id', '=', values["saving_plan_id"]),
                                      ('state_plan','=',values['state_plan']),
                                     ('old_ref_id','=',values["old_ref_id"])
                                     ])
        try:
            if nombre not in procesados:
                if not srch_plan:
                    srch_plan = OBJ_PLAN.create(values)
                    srch_plan=srch_plan.with_context({"pass_validate":True})
                    if srch_plan.state_plan=='close':
                        srch_plan.action_close()
                    if srch_plan.state_plan in ('cancelled','anulled'):
                        srch_plan.action_cancel()
                    if srch_plan.state_plan not in ('draft','cancelled','anulled','close'):
                        srch_plan.action_open()
                    self._cr.commit()
                else:
                    if srch_plan.state=='draft':
                        srch_plan.write(values)
                        self._cr.commit()

            mensajes.append((values["old_ref_id"],nombre, str(values), "ok"))
            procesados.append(values["old_ref_id"])
        except Exception as e:
            error_msg = f"Error en {nombre}: {str(e)}"
            print(error_msg)
            mensajes.append((values["old_ref_id"],nombre, error_msg,"error"))  # Guardar error
            #self._cr.rollback()
        return srch_plan

    def process_file(self):
        """ Procesa el archivo Excel """
        # Definir índices de columnas
        OBJ_PARTNER=self.env["res.partner"].sudo()
        OBJ_JOURNAL = self.env["account.journal"].sudo()
        OBJ_PLAN= self.env["account.saving.plan"].sudo()

        NOMBRE = 0
        SOCIO_CEDULA = 1
        SOCIO = 2
        TIPO_DE_AHORRO = 3
        INICIO = 4
        FINALIZACION = 5
        MONTO_DE_AHORRO = 6
        NUM_DOCUMENTOS = 7
        NUM_PAGOS = 8
        VENDEDOR = 9
        COMPANIA = 10
        ESTADO = 11
        LINEA_NUM = 12
        LINEA_FECHA = 13
        LINEA_APORTACIONES = 14
        LINEA_ACUMULADO = 15
        LINEA_PLANES_AHORRO = 16

        LINEA_PAGOS = 17
        LINEA_PENDIENTE = 18

        LINEA_FECHA_DE_PAGO = 19
        LINEA_ESTADO_DE_PAGO = 20
        GASTOS_DE_PRODUCTOS_NOMBRE = 21
        DIARIO_DESHABILITADOS_NOMBRE_DEL_DIARIO = 22
        CUENTA_DE_TRANSITO = 23
        PRODUCTO_DE_SEGUROS = 24
        PRODUCTO_DE_INSCRIPCION = 25
        PRODUCTO_DE_DESCUENTO = 26
        DIARIO_NOMBRE = 27
        TIPO_DOCUMENTO = 28
        DIARIO_DESHABILITADOS_NOMBRE_MOSTRADO = 29
        PLAN_AHORRO_ANT_ID=30
        CANTIDAD_FIJA=31
        IMPORTE_CUOTA=32
        PERIODOS = 33
        CUENTA_ANALITICO=34
        TASA_INSCRIPCION=35
        TASA_GASTOS = 36
        TASA_SEGURO=37
        TASA_DECRECIMIENT=38
        CENTRO = 39
        TIENE_FACTURAS=40
        PAGOS=41

        LINEA_SERV_ADMIN=42
        LINEA_SEGURO = 43

        ANT_REF = 44
        LINEA_ANT_REF = 45

        DEC=2
        mensajes = []  # Lista para almacenar mensajes

        for brw_each in self:
            ext = self.get_ext(brw_each.file_name)
            fileName = self.create_file(ext)
            self.write_file(fileName, brw_each.file, modeWrite="wb")

            book = xlrd.open_workbook(fileName)
            sheet = book.sheet_by_index(0)

            values = {}
            last_name = False
            ant_plan_id=""
            procesados=[]
            old_payment_id=False
            for row_index in range(1, sheet.nrows):  # Saltamos encabezados
                try:
                    nombre = sheet.cell(row_index, NOMBRE).value
                    socio_cedula = sheet.cell(row_index, SOCIO_CEDULA).value
                    socio = sheet.cell(row_index, SOCIO).value


                    tipo_de_ahorro = sheet.cell(row_index, TIPO_DE_AHORRO).value
                    inicio = sheet.cell(row_index, INICIO).value
                    finalizacion = sheet.cell(row_index, FINALIZACION).value
                    monto_de_ahorro = sheet.cell(row_index, MONTO_DE_AHORRO).value



                    num_documentos = sheet.cell(row_index, NUM_DOCUMENTOS).value
                    num_pagos = sheet.cell(row_index, NUM_PAGOS).value
                    vendedor = sheet.cell(row_index, VENDEDOR).value
                    compania = sheet.cell(row_index, COMPANIA).value
                    estado = sheet.cell(row_index, ESTADO).value

                    linea_num = sheet.cell(row_index, LINEA_NUM).value
                    linea_fecha = sheet.cell(row_index, LINEA_FECHA).value
                    linea_aportaciones = sheet.cell(row_index, LINEA_APORTACIONES).value
                    linea_acumulado = sheet.cell(row_index, LINEA_ACUMULADO).value
                    linea_planes_ahorro = sheet.cell(row_index, LINEA_PLANES_AHORRO).value

                    linea_fecha_de_pago = sheet.cell(row_index, LINEA_FECHA_DE_PAGO).value
                    linea_estado_de_pago = sheet.cell(row_index, LINEA_ESTADO_DE_PAGO).value
                    gastos_de_productos_nombre = sheet.cell(row_index, GASTOS_DE_PRODUCTOS_NOMBRE).value
                    diario_deshabilitados_nombre = sheet.cell(row_index, DIARIO_DESHABILITADOS_NOMBRE_DEL_DIARIO).value
                    cuenta_de_transito = sheet.cell(row_index, CUENTA_DE_TRANSITO).value
                    producto_de_seguros = sheet.cell(row_index, PRODUCTO_DE_SEGUROS).value
                    producto_de_inscripcion = sheet.cell(row_index, PRODUCTO_DE_INSCRIPCION).value
                    producto_de_descuento = sheet.cell(row_index, PRODUCTO_DE_DESCUENTO).value
                    diario_nombre = sheet.cell(row_index, DIARIO_NOMBRE).value
                    tipo_documento = sheet.cell(row_index, TIPO_DOCUMENTO).value
                    diario_deshabilitados_nombre_mostrado = sheet.cell(row_index,
                                                                       DIARIO_DESHABILITADOS_NOMBRE_MOSTRADO).value
                    ant_plan_id=sheet.cell(row_index, PLAN_AHORRO_ANT_ID).value

                    cantidad_fija = sheet.cell(row_index, CANTIDAD_FIJA).value
                    importe_cuota = sheet.cell(row_index, IMPORTE_CUOTA).value

                    periodos = sheet.cell(row_index, PERIODOS).value

                    cuenta_analitica = sheet.cell(row_index, CUENTA_ANALITICO).value
                    tasa_inscripcion = sheet.cell(row_index, TASA_INSCRIPCION).value
                    tasa_gastos = sheet.cell(row_index, TASA_GASTOS).value
                    tasa_seguro = sheet.cell(row_index, TASA_SEGURO).value
                    tasa_decrecimiento = sheet.cell(row_index, TASA_DECRECIMIENT).value

                    centro = sheet.cell(row_index, CENTRO).value

                    tiene_facturas = sheet.cell(row_index, TIENE_FACTURAS).value
                    linea_pagos = sheet.cell(row_index, LINEA_PAGOS).value

                    linea_serv_admin = sheet.cell(row_index, LINEA_SERV_ADMIN).value
                    linea_seguro = sheet.cell(row_index, LINEA_SEGURO).value

                    ant_ref = sheet.cell(row_index, ANT_REF).value

                    linea_ant_ref = sheet.cell(row_index, LINEA_ANT_REF).value
                    ##############
                    base_date = datetime(1899, 12, 30)  # Excel cuenta incorrectamente 1900 como bisiesto

                    # Convertir número de serie a fecha
                    fecha_cuota = base_date + timedelta(days=linea_fecha)

                    line_values = (0, 0, {
                        "sequence": linea_num ,
                        "number": linea_num+1,
                        "date": fecha_cuota,

                        "saving_amount": linea_aportaciones,
                        "principal_amount": linea_planes_ahorro,
                        "serv_admin_percentage": (linea_num == 0) and tasa_inscripcion or tasa_gastos,
                        "seguro_percentage": tasa_seguro,

                        "serv_admin_amount": linea_serv_admin,
                        "seguro_amount": linea_seguro,

                        "migrated": True,
                        "migrated_has_invoices": tiene_facturas,
                        "migrated_payment_amount": linea_pagos,
                        "old_ref_id":linea_ant_ref

                    })
                    #print(line_values)
                    ##############
                    if not nombre:  # Línea de subdetalle
                        values.setdefault("line_ids", [(5,)]).append(line_values)
                    else:  # Nueva transacción
                        if nombre and last_name and last_name!=nombre:
                            self.ejecutar_transaccion(last_name, values,procesados, mensajes)
                            #break

                        if socio_cedula:
                            srch_socio = OBJ_PARTNER.search([('vat', '=', socio_cedula)])
                            if not srch_socio:
                                srch_socio = OBJ_PARTNER.search([('name', '=', socio)])
                                if not srch_socio:
                                    srch_socio = OBJ_PARTNER.create({
                                        "vat": socio_cedula,
                                        "name": socio
                                    })
                                else:
                                    srch_socio = srch_socio[0]
                            else:
                                srch_socio=srch_socio[0]
                        srch_ahorro_plan = OBJ_PLAN.search([('saving_type', '=', tipo_de_ahorro.lower()),
                                                            ('old_id', '=',ant_plan_id)
                                                            ])
                        if not srch_ahorro_plan:
                            mensajes.append((ant_plan_id,nombre, "", "NO EXISTE PLAN DE AHORRO"))
                            continue
                        seller_srch=self.env["res.users"].sudo().search([('name','=',vendedor)])
                        if not seller_srch:
                            seller_srch=self.env.user
                        else:
                            seller_srch=seller_srch[0]

                        base_date = datetime(1899, 12, 30)  # Excel cuenta incorrectamente 1900 como bisiesto

                        # Convertir número de serie a fecha
                        start_date = base_date + timedelta(days=inicio)
                        end_date = base_date + timedelta(days=finalizacion)
                        #print(converted_date.strftime("%Y-%m-%d"))
                        srch_journal=OBJ_JOURNAL
                        if centro and diario_nombre:
                            diario_final="%s Facturas de cliente" % (centro,)
                            srch_journal=OBJ_JOURNAL.search([('type','=','sale'),('name','=',diario_final)])
                            # if not srch_journal:
                            #     mensajes.append((nombre, "", "%s NO EXISTE" % (diario_final,)) )
                            #     continue
                        values = {
                            "name": nombre,
                            'saving_type':tipo_de_ahorro.lower(),
                            'saving_plan_id':srch_ahorro_plan[0].id,
                            'partner_id':srch_socio.id,
                            'seller_id':seller_srch.id,
                            "start_date":start_date,
                            "end_date": end_date,
                            'company_id':brw_each.company_id.id,
                            'info_migrate':True,
                            'periods':periodos,
                            'saving_amount':monto_de_ahorro,
                            'fixed_amount':cantidad_fija,
                            'quota_amount': importe_cuota,
                            "state": 'draft',
                            'state_plan':status_dict_inverted[estado],
                            "rate_inscription":tasa_inscripcion,
                            "rate_expense": tasa_gastos,
                            "rate_insurance": tasa_seguro,
                            "rate_decrement_year": tasa_decrecimiento,
                            "document_type_id":self.env.ref("l10n_ec.ec_dt_01").id,
                            "journal_id":srch_journal and srch_journal.id or False,
                            "old_ref_id":ant_ref,
                            "line_ids": [(5,),line_values]  # Para almacenar las líneas asociadas
                        }
                    if nombre:
                        last_name = nombre

                except Exception as e:
                    error_msg = f"Error en fila {row_index}: {str(e)}"
                    mensajes.append((ant_plan_id,"Fila " + str(row_index),"", error_msg))

            if last_name:
                #print(last_name)
                self.ejecutar_transaccion(last_name, values,procesados, mensajes)
                #break

        # Guardar mensajes en un archivo Excel
        #print(mensajes)
        archivo=self.guardar_mensajes(mensajes)
        self.write({"file_name_result":"mensajes.xlsx",
                            "file_result":archivo
                            })
        return True

    def process_payments(self):
        """ Procesa el archivo Excel """
        # Definir índices de columnas
        OBJ_PARTNER = self.env["res.partner"].sudo()
        OBJ_JOURNAL = self.env["account.journal"].sudo()
        OBJ_LINE_PAYMENT = self.env["account.saving.line.payment"].sudo()

        LINEA_AHORRO_ID = 0
        AHORRO_ID = 1
        AHORRO_NOMBRE_MOSTRADO = 2
        FECHA = 3
        DIARIO = 4
        FECHA_FACTURA = 5
        NUMERO_FACTURA = 6
        CLIENTE_PROVEEDOR = 7
        REFERENCIA = 8
        CUOTAS = 9
        IMPORTE = 10
        EMPRESA = 11
        ESTADO = 12
        CUOTAS_ID = 13

        CUOTAS_PAGOS = 14
        CUOTAS_PENDIENTE = 15
        CUOTAS_VALOR = 16

        LINEA_AHORRO_REF_ID = 17
        CUOTA_REF_ID=18

        PAGO_REF=19
        APPLY_LINEA_AHORRO_REF_ID = 20

        DEC = 2
        mensajes = []  # Lista para almacenar mensajes

        for brw_each in self:
            ext = self.get_ext(brw_each.file_payment_name)
            fileName = self.create_file(ext)
            self.write_file(fileName, brw_each.file_payment, modeWrite="wb")

            book = xlrd.open_workbook(fileName)
            sheet = book.sheet_by_index(0)

            values = {}
            last_name = False
            procesados = []
            linea_ref=False
            fecha_pago=False
            pago_ref=False
            old_payment_id=False
            for row_index in range(1, sheet.nrows):  # Saltamos encabezados
                try:
                    linea_ahorro_id = sheet.cell(row_index, LINEA_AHORRO_ID).value
                    ahorro_id = sheet.cell(row_index, AHORRO_ID).value
                    ahorro_nombre_mostrado = sheet.cell(row_index, AHORRO_NOMBRE_MOSTRADO).value
                    fecha = sheet.cell(row_index, FECHA).value
                    diario = sheet.cell(row_index, DIARIO).value
                    fecha_factura = sheet.cell(row_index, FECHA_FACTURA).value
                    numero_factura = sheet.cell(row_index, NUMERO_FACTURA).value
                    cliente_proveedor = sheet.cell(row_index, CLIENTE_PROVEEDOR).value
                    referencia = sheet.cell(row_index, REFERENCIA).value
                    cuotas = sheet.cell(row_index, CUOTAS).value
                    importe = sheet.cell(row_index, IMPORTE).value
                    empresa = sheet.cell(row_index, EMPRESA).value
                    estado = sheet.cell(row_index, ESTADO).value
                    linea_id = sheet.cell(row_index, CUOTAS_ID).value

                    cuotas_pago = sheet.cell(row_index, CUOTAS_PAGOS).value
                    cuotas_pendiente = sheet.cell(row_index, CUOTAS_PENDIENTE).value
                    cuotas_valor = sheet.cell(row_index, CUOTAS_VALOR).value

                    linea_ref = sheet.cell(row_index, LINEA_AHORRO_REF_ID).value

                    cuota_ref = sheet.cell(row_index, CUOTA_REF_ID).value

                    pago_ref = sheet.cell(row_index, PAGO_REF).value

                    aplicado_linea_ref = sheet.cell(row_index, APPLY_LINEA_AHORRO_REF_ID).value

                    if len(pago_ref)>0 and len(linea_ref)>0:  ###es el primero
                        print(pago_ref)
                        base_date = datetime(1899, 12, 30)  # Excel cuenta incorrectamente 1900 como bisiesto

                        # Convertir número de serie a fecha
                        fecha_pago = base_date + timedelta(days=fecha)

                        saving_line_id = self.env["account.saving.lines"].search([('old_ref_id', '=', linea_ref)])
                        if saving_line_id:
                            payment_line_values = {
                                "type": "historic",
                                "payment_date": fecha_pago,
                                "payment_ref": referencia,
                                "payment_journal_name": diario,
                                "amount": importe,
                                "old_ref_id": pago_ref,
                                "saving_line_id": saving_line_id.id,
                                "saving_id": saving_line_id.saving_id.id,
                                "payment_state": estado,
                                "line_ids":[(5,)]
                            }
                            old_payment_id=self.ejecutar_pago_transaccion(pago_ref, payment_line_values, procesados, mensajes)
                            last_name=False
                            if aplicado_linea_ref and cuotas_valor:
                                srch_apply_lines= self.env["account.saving.lines"].search([('old_ref_id', '=', aplicado_linea_ref)])
                                print("recien lo crea")
                                brw_lines_payment=OBJ_LINE_PAYMENT.create({
                                    "saving_id":srch_apply_lines.saving_id.id,
                                    "type":"historic",
                                    "number":srch_apply_lines.number,
                                    "date":srch_apply_lines.date,
                                    "saving_line_id":srch_apply_lines.id,
                                    "pendiente":importe,
                                    "aplicado":cuotas_valor,
                                    "old_ref_id":cuota_ref,
                                    "old_payment_id":old_payment_id.id,
                                })
                                old_payment_id=brw_lines_payment
                                last_name = pago_ref
                        else:
                            mensajes.append((pago_ref,"Fila " + str(row_index), "", linea_ref+" no fue encontrado"))
                        # if pago_ref:
                        #     if nombre and last_name and last_name != nombre:
                        #         last_name = pago_ref
                        #         old_payment_id = False
                    else:#crear enlace pagos cuotas
                        print("fila vacia")
                        if last_name:
                            srch_lines =  self.env["account.saving.payment"].sudo().search([
                                ('old_ref_id', '=', last_name)
                            ])
                            srch_apply_lines = self.env["account.saving.lines"].sudo().search(
                                [('old_ref_id', '=', aplicado_linea_ref)])

                            old_payment_id=srch_lines
                            if not old_payment_id:
                                mensajes.append((aplicado_linea_ref, "Fila " + str(row_index), "", aplicado_linea_ref + " pago no fue encontrado"))
                                continue
                            print(aplicado_linea_ref,srch_apply_lines)
                            #if not srch_apply_lines:
                            #    raise ValidationError("xxxx")
                            brw_lines_payment = OBJ_LINE_PAYMENT.create({
                                "saving_id": srch_apply_lines.saving_id.id,
                                "type": "historic",
                                "number": srch_apply_lines.number,
                                "date": srch_apply_lines.date,
                                "saving_line_id": srch_apply_lines.id,
                                "pendiente": importe,
                                "aplicado": cuotas_valor,
                                "old_ref_id": cuota_ref,
                                "old_payment_id": old_payment_id.id,
                            })
                            print("fila vacia",brw_lines_payment)



                except Exception as e:
                    error_msg = f"Error en fila {row_index}: {str(e)}"
                    mensajes.append((pago_ref,"Fila " + str(row_index), "", error_msg))

        archivo = self.guardar_mensajes(mensajes)
        self.write({"file_payment_name_result": "mensajes_pagos.xlsx",
                    "file_payment_result": archivo
                    })
        return True

    def ejecutar_pago_transaccion(self, nombre, values,procesados, mensajes):
        """ Ejecuta la transacción y guarda mensajes si los hay """
        OBJ_PAYMENTS = self.env["account.saving.payment"].sudo()
        #print(values)
        srch_lines= OBJ_PAYMENTS.search([
                                     ('old_ref_id','=',nombre)
                                     ])
        try:
            if nombre not in procesados:
                if not srch_lines:
                    print("al crer",values)
                    srch_lines=OBJ_PAYMENTS.create(values)
                    print("cera",srch_lines)
                    self._cr.commit()
                else:
                    srch_lines.write(values)
                    self._cr.commit()
                    print("actualziado")
            mensajes.append((nombre,nombre, str(values), "ok"))
            procesados.append(nombre)
        except Exception as e:
            error_msg = f"Error en {nombre}: {str(e)}"
            print("error",error_msg)
            mensajes.append((nombre,nombre, error_msg,"error"))  # Guardar error
            #self._cr.rollback()
        return srch_lines
