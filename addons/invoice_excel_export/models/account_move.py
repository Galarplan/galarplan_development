# -*- coding: utf-8 -*-

from odoo import models
from odoo.exceptions import UserError
import io
import base64
import xlsxwriter
import xml.etree.ElementTree as ET
from xml.dom import minidom


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_export_invoice_excel(self):

        self.ensure_one()

        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet("Factura")

        header_format = workbook.add_format({
            'bold': True,
            'border': 1
        })

        normal_format = workbook.add_format({
            'border': 1
        })

        headers = [
            'rucComercializador',
            'CAMV/Cpn',
            'serialVin',
            'nombrePropietario',
            'tipoIdentificacionPropietario',
            'numeroDocumentoPropietario',
            'tipoComprobante',
            'establecimientoComprobante',
            'emisionComprobante',
            'numeroComprobante',
            'numeroAutorizacion',
            'fechaVenta',
            'precioVenta',
            'codigoCantonMatriculacion',
            'tipo',
            'calle',
            'numero',
            'intersección',
            'provincia',
            'numero2'
        ]

        # =====================================================
        # FILAS SUPERIORES
        # =====================================================

        sheet.write(
            0,
            0,
            'numeroRUC',
            header_format
        )

        sheet.write(
            1,
            0,
            self.company_id.vat or '',
            normal_format
        )

        # =====================================================
        # CABECERAS
        # =====================================================

        row = 2

        for col, header in enumerate(headers):
            sheet.write(row, col, header, header_format)

        row += 1

        partner = self.partner_id

        # =====================================================
        # TIPO IDENTIFICACION
        # =====================================================

        tipo_identificacion = ''

        if partner.l10n_latam_identification_type_id:

            if partner.l10n_latam_identification_type_id.name == 'RUC':
                tipo_identificacion = 'R'

            elif partner.l10n_latam_identification_type_id.name == 'Cédula':
                tipo_identificacion = 'C'

        # =====================================================
        # ESTABLECIMIENTO / EMISION
        # =====================================================

        establecimiento = ''
        emision = ''

        sequence_prefix = self.sequence_prefix or ''

        # quitar "Fact "
        sequence_prefix = sequence_prefix.replace('Fact ', '')

        # separar por "-"
        sequence_parts = sequence_prefix.split('-')

        if len(sequence_parts) >= 1:
            establecimiento = sequence_parts[0]

        if len(sequence_parts) >= 2:
            emision = sequence_parts[1]

        # =====================================================
        # BUSCAR VEHICULO
        # =====================================================

        serial_vin = ''
        camv_cpn = ''

        if self.is_vehicle:

            for line in self.invoice_line_ids:

                # obtener product.product de la línea
                product = line.product_id

                if not product:
                    continue

                # obtener product.template relacionado
                template = product.product_tmpl_id

                if not template:
                    continue

                # llenar variables desde product.template
                serial_vin = template.chassis_number or ''
                camv_cpn = template.ramw_number or ''

                # si encontró datos, salir
                if serial_vin or camv_cpn:
                    break

        # =====================================================
        # TIPO
        # =====================================================

        tipo = 'OTRO'

        if partner.type == 'contact':
            tipo = 'RESIDENCIA'

        elif partner.type == 'invoice':
            tipo = 'OFICINA'

        # =====================================================
        # ESCRIBIR DATOS
        # =====================================================

        sheet.write(
            row,
            0,
            self.company_id.vat or '',
            normal_format
        )

        sheet.write(
            row,
            1,
            camv_cpn,
            normal_format
        )

        sheet.write(
            row,
            2,
            serial_vin,
            normal_format
        )

        sheet.write(
            row,
            3,
            partner.name or '',
            normal_format
        )

        sheet.write(
            row,
            4,
            tipo_identificacion,
            normal_format
        )

        sheet.write(
            row,
            5,
            partner.vat or '',
            normal_format
        )

        sheet.write(
            row,
            6,
            '1',
            normal_format
        )

        sheet.write(
            row,
            7,
            establecimiento,
            normal_format
        )

        sheet.write(
            row,
            8,
            emision,
            normal_format
        )

        sheet.write(
            row,
            9,
            (self.name or '').replace('Fact ', '')[-9:],
            normal_format
        )

        sheet.write(
            row,
            10,
            self.l10n_ec_authorization_number or '',
            normal_format
        )

        sheet.write(
            row,
            11,
            self.invoice_date.strftime('%d-%m-%Y')
            if self.invoice_date else '',
            normal_format
        )

        sheet.write(
            row,
            12,
            self.amount_total or 0.0,
            normal_format
        )

        sheet.write(
            row,
            13,
            '10901',
            normal_format
        )

        sheet.write(
            row,
            14,
            tipo,
            normal_format
        )

        sheet.write(
            row,
            15,
            partner.street or '',
            normal_format
        )

        sheet.write(
            row,
            16,
            '0',
            normal_format
        )

        sheet.write(
            row,
            17,
            'NP',
            normal_format
        )

        sheet.write(
            row,
            18,
            '109',
            normal_format
        )

        sheet.write(
            row,
            19,
            partner.phone or '',
            normal_format
        )

        # =====================================================
        # GENERAR ARCHIVO
        # =====================================================

        workbook.close()

        output.seek(0)

        file_data = base64.b64encode(output.read())

        attachment = self.env['ir.attachment'].create({
            'name': 'Factura_%s.xlsx' % (self.name or ''),
            'type': 'binary',
            'datas': file_data,
            'res_model': 'account.move',
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        output.close()

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }
    def action_export_invoice_xml(self):
        self.ensure_one()

        # =====================================================
        # CREAR ESTRUCTURA XML
        # =====================================================

        ventas = ET.Element("ventas")

        datos_registrador = ET.SubElement(
            ventas,
            "datosRegistrador"
        )

        ET.SubElement(
            datos_registrador,
            "numeroRUC"
        ).text = self.company_id.vat or ""    

        # =====================================================
        # DATOS DE LA VENTA
        # =====================================================

        datos_ventas = ET.SubElement(
            ventas,
            "datosVentas"
        )

        venta = ET.SubElement(
            datos_ventas,
            "venta"
        )        

        # =====================================================
        # DATOS GENERALES FACTURA
        # =====================================================

        partner = self.partner_id


        # =====================================================
        # TIPO IDENTIFICACION
        # =====================================================

        tipo_identificacion = ""

        if partner.l10n_latam_identification_type_id:

            if partner.l10n_latam_identification_type_id.name == 'RUC':
                tipo_identificacion = 'R'

            elif partner.l10n_latam_identification_type_id.name == 'Cédula':
                tipo_identificacion = 'C'


        # =====================================================
        # BUSCAR VEHICULO
        # =====================================================

        serial_vin = ""
        camv_cpn = ""

        if self.is_vehicle:

            for line in self.invoice_line_ids:

                product = line.product_id

                if not product:
                    continue

                template = product.product_tmpl_id

                if not template:
                    continue

                serial_vin = template.chassis_number or ""
                camv_cpn = template.ramw_number or ""

                if serial_vin or camv_cpn:
                    break

        # =====================================================
        # DATOS VEHICULO / PROPIETARIO
        # =====================================================

        ET.SubElement(
            venta,
            "rucComercializador"
        ).text = self.company_id.vat or ""


        ET.SubElement(
            venta,
            "CAMVCpn"
        ).text = camv_cpn


        ET.SubElement(
            venta,
            "serialVin"
        ).text = serial_vin


        ET.SubElement(
            venta,
            "nombrePropietario"
        ).text = partner.name or ""


        ET.SubElement(
            venta,
            "tipoIdentificacionPropietario"
        ).text = tipo_identificacion


        ET.SubElement(
            venta,
            "numeroDocumentoPropietario"
        ).text = partner.vat or ""     

        # =====================================================
        # DATOS COMPROBANTE SRI
        # =====================================================

        establecimiento = ""
        emision = ""

        sequence_prefix = self.sequence_prefix or ""

        # quitar "Fact "
        sequence_prefix = sequence_prefix.replace('Fact ', '')

        sequence_parts = sequence_prefix.split('-')


        if len(sequence_parts) >= 1:
            establecimiento = sequence_parts[0]


        if len(sequence_parts) >= 2:
            emision = sequence_parts[1]

        ET.SubElement(
            venta,
            "tipoComprobante"
        ).text = "1"


        ET.SubElement(
            venta,
            "establecimientoComprobante"
        ).text = establecimiento


        ET.SubElement(
            venta,
            "puntoEmisionComprobante"
        ).text = emision


        ET.SubElement(
            venta,
            "numeroComprobante"
        ).text = (self.name or '').replace('Fact ', '')[-9:]


        ET.SubElement(
            venta,
            "numeroAutorizacion"
        ).text = self.l10n_ec_authorization_number or ""


        ET.SubElement(
            venta,
            "fechaVenta"
        ).text = (
            self.invoice_date.strftime('%d-%m-%Y')
            if self.invoice_date
            else ""
        )


        ET.SubElement(
            venta,
            "precioVenta"
        ).text = str(int(self.amount_total or 0))

        ET.SubElement(
            venta,
            "codigoCantonMatriculacion"
        ).text = "0901"        

        # =====================================================
        # DIRECCION
        # =====================================================

        datos_direccion = ET.SubElement(
            venta,
            "datosDireccion"
        )


        tipo = "OTRO"

        if partner.type == 'contact':
            tipo = "RESIDENCIA"

        elif partner.type == 'invoice':
            tipo = "OFICINA"


        ET.SubElement(
            datos_direccion,
            "tipo"
        ).text = tipo


        ET.SubElement(
            datos_direccion,
            "calle"
        ).text = partner.street or ""


        ET.SubElement(
            datos_direccion,
            "numero"
        ).text = "0"


        ET.SubElement(
            datos_direccion,
            "interseccion"
        ).text = "NP"

        # =====================================================
        # TELEFONO
        # =====================================================

        datos_telefono = ET.SubElement(
            venta,
            "datosTelefono"
        )


        ET.SubElement(
            datos_telefono,
            "provincia"
        ).text = (
            partner.state_id.code
            if partner.state_id
            else ""
        )


        ET.SubElement(
            datos_telefono,
            "numero"
        ).text = partner.phone or ""

        # =====================================================
        # GENERAR ARCHIVO XML
        # =====================================================

        xml_bytes = ET.tostring(
            ventas,
            encoding="utf-8"
        )


        xml_pretty = minidom.parseString(
            xml_bytes
        ).toprettyxml(
            indent="    ",
            encoding="utf-8"
        )

        # =====================================================
        # CREAR ADJUNTO
        # =====================================================

        file_data = base64.b64encode(
            xml_pretty
        )


        attachment = self.env["ir.attachment"].create({

            "name": "Factura_%s.xml" % (
                self.name or ""
            ),

            "type": "binary",

            "datas": file_data,

            "res_model": "account.move",

            "res_id": self.id,

            "mimetype": "application/xml",
        })

        # =====================================================
        # DESCARGAR ARCHIVO
        # =====================================================

        return {
            "type": "ir.actions.act_url",

            "url": "/web/content/%s?download=true"
                   % attachment.id,

            "target": "self",
        }

        pass