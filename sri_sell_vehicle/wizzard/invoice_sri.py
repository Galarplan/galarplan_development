# -*- coding: utf-8 -*-
from odoo import models, fields, api
import xml.etree.ElementTree as ET
from io import BytesIO
import base64
import pandas as pd
from datetime import datetime

class WizardGenerateXmlExcel(models.TransientModel):
    _name = 'wizard.generate.xml.excel'
    _description = 'Wizard to generate XML or Excel'

    date_from = fields.Date(string='Fecha Desde', required=True)
    date_to = fields.Date(string='Fecha Hasta', required=True)
    invoice_ids = fields.One2many(
        comodel_name='wizard.generate.xml.excel.line',
        inverse_name='wizard_id',
        string='Facturas de Ventas',
        help='Seleccione las facturas de venta que desea procesar.'
    )
    empresa_id = fields.Many2one('res.company',string = 'Compañia', default = lambda self : self.env.company.id)

    def load_invoices(self):
        """Cargar las facturas en el rango de fechas seleccionado."""
        invoices = self.env['account.move'].search([
            ('state', '=', 'posted'),
            ('move_type', '=', 'out_invoice'),
            ('invoice_date', '>=', self.date_from),
            ('company_id', '=', self.empresa_id.id),
            ('invoice_date', '<=', self.date_to),
            ('is_vehicle', '=', True),
        ])

        lines = []
        for invoice in invoices:
            for product_line in invoice.invoice_line_ids:
                lines.append((0, 0, {
                    'ruc_empresa': self.empresa_id.vat,
                    'serialvin': product_line.product_id.chassis_number,
                    'identification_type': invoice.partner_id.l10n_latam_identification_type_id.name,
                    'identification_number' : invoice.partner_id.vat,
                    'tipo_comprobante' : invoice.l10n_latam_document_type_id.id,
                    'estblecimiento': invoice.journal_id.l10n_ec_entity,
                    'punto_emision' : invoice.journal_id.l10n_ec_emission,
                    'numero_comprobante' : invoice.l10n_latam_document_number.split('-')[2],
                    'numero_autorizacion' : invoice.l10n_ec_authorization_number,
                    'fecha_venta' : invoice.invoice_date,
                    'precio_venta': product_line.price_unit,
                    'codigo_canton' : invoice.partner_id.country_substate_id.code,
                    'tipo_vivienda' : invoice.partner_id.residence_type,
                    'street': invoice.partner_id.street,
                    'calle': invoice.partner_id.address_number,
                    'interseccion': invoice.partner_id.intersection,
                    'provincia' : invoice.partner_id.state_id.country_state_code,
                    'celular' : invoice.partner_id.mobile,
                    # 'invoice_id': invoice.id,
                    'partner_id': invoice.partner_id.id,
                    # 'invoice_date': invoice.invoice_date,
                    # 'amount_total': invoice.amount_total,
                })) 

        self.invoice_ids = lines

        # Retornar una acción para recargar el wizard y evitar que se cierre
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }


    def generate_xml(self):
        """Generate XML file where each record is an independent <ventas> node"""
        xml_blocks = []  # Lista para almacenar cada nodo raíz independiente

        # Generar un nodo de <ventas> por cada línea
        for line in self.invoice_ids:
            ventas = ET.Element('ventas')
            ET.SubElement(ventas, 'rucComercializador').text = line.ruc_empresa or ''
            ET.SubElement(ventas, 'serialVin').text = line.serialvin or ''
            ET.SubElement(ventas, 'nombrePropietario').text = line.partner_id.name or ''
            ET.SubElement(ventas, 'tipoIdentificacionPropietario').text = line.identification_type or ''
            ET.SubElement(ventas, 'numeroDocumentoPropietario').text = line.identification_number or ''
            ET.SubElement(ventas, 'tipoComprobante').text = str(line.tipo_comprobante or '')
            ET.SubElement(ventas, 'establecimientoComprobante').text = line.estblecimiento or ''
            ET.SubElement(ventas, 'puntoEmisionComprobante').text = line.punto_emision or ''
            ET.SubElement(ventas, 'numeroComprobante').text = line.numero_comprobante or ''
            ET.SubElement(ventas, 'numeroAutorizacion').text = line.numero_autorizacion or ''
            ET.SubElement(ventas, 'fechaVenta').text = line.fecha_venta.strftime('%d-%m-%Y') if line.fecha_venta else ''
            ET.SubElement(ventas, 'precioVenta').text = str(line.precio_venta or '')
            ET.SubElement(ventas, 'codigoCantonMatriculacion').text = line.codigo_canton or ''
            ET.SubElement(ventas, 'tipo').text = line.tipo_vivienda or ''
            ET.SubElement(ventas, 'calle').text = line.street or ''
            ET.SubElement(ventas, 'numero').text = line.calle or ''
            ET.SubElement(ventas, 'interseccion').text = line.interseccion or ''
            ET.SubElement(ventas, 'provincia').text = line.provincia or ''
            ET.SubElement(ventas, 'celular').text = line.celular or ''

            # Convertir cada nodo <ventas> en un bloque XML independiente
            xml_blocks.append(ET.tostring(ventas, encoding='utf-8', method='xml').decode('utf-8'))

        # Combinar todos los bloques en un solo archivo
        final_xml_content = '\n'.join(xml_blocks)

        # Crear archivo con nombre único basado en timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_name = f'ventas_{timestamp}.xml'

        # Guardar el archivo como adjunto
        attachment = self.env['ir.attachment'].create({
            'name': file_name,
            'datas': base64.b64encode(final_xml_content.encode('utf-8')),
            'type': 'binary',
            'res_model': 'wizard.generate.xml.excel',
            'res_id': self.id,
        })

        # Descargar el archivo
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }


    def generate_excel(self):
        """Generate Excel file with column names matching XML fields"""
        data = []
        for line in self.invoice_ids:
            data.append({
                'rucComercializador': line.ruc_empresa or '',
                'serialVin': line.serialvin or '',
                'nombrePropietario': line.partner_id.name or '',
                'tipoIdentificacionPropietario': line.identification_type or '',
                'numeroDocumentoPropietario': line.identification_number or '',
                'tipoComprobante': str(line.tipo_comprobante or ''),
                'establecimientoComprobante': line.estblecimiento or '',
                'puntoEmisionComprobante': line.punto_emision or '',
                'numeroComprobante': line.numero_comprobante or '',
                'numeroAutorizacion': line.numero_autorizacion or '',
                'fechaVenta': line.fecha_venta.strftime('%d-%m-%Y') if line.fecha_venta else '',
                'precioVenta': line.precio_venta or 0.0,
                'codigoCantonMatriculacion': line.codigo_canton or '',
                'tipo': line.tipo_vivienda or '',
                'calle': line.street or '',
                'numero': line.calle or '',
                'interseccion': line.interseccion or '',
                'provincia': line.provincia or '',
                'celular': line.celular or '',
            })

        # Crear archivo Excel
        df = pd.DataFrame(data)
        output = BytesIO()
        df.to_excel(output, index=False, sheet_name='Ventas')
        file_data = output.getvalue()
        output.close()

        # Crear archivo con nombre único basado en timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_name = f'ventas_{timestamp}.xlsx'

        # Guardar el archivo como adjunto
        attachment = self.env['ir.attachment'].create({
            'name': file_name,
            'datas': base64.b64encode(file_data),
            'type': 'binary',
            'res_model': 'wizard.generate.xml.excel',
            'res_id': self.id,
        })

        # Descargar el archivo
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }



class WizardGenerateXmlExcelLine(models.TransientModel):
    _name = 'wizard.generate.xml.excel.line'
    _description = 'Lines for Wizard Generate XML/Excel'



    wizard_id = fields.Many2one('wizard.generate.xml.excel', string='Wizard')
    ruc_empresa = fields.Char(string='rucComercializador')
    camvcpn = fields.Char(string='CAMV/Cpn')
    serialvin = fields.Char(string='serialVin')
    partner_id = fields.Many2one('res.partner', string='nombrePropietario')
    identification_type = fields.Char(string='tipoidentificacionPropietario')
    identification_number = fields.Char(string='numeroDocumentoPropietario')
    tipo_comprobante = fields.Integer(string='tipoComprobante')
    estblecimiento = fields.Char(string='estableciminetoComprobante')
    punto_emision = fields.Char(string='puntoEmisionComprobante')
    numero_comprobante = fields.Char(string='numeroComprobante')
    numero_autorizacion = fields.Char(string='numeroAutorizacion')
    fecha_venta = fields.Date(string='fechaVenta')
    precio_venta = fields.Float(string='precioVenta')
    codigo_canton = fields.Char(string='codigoCantonMatriculacion')
    tipo_vivienda = fields.Char(string='tipo')
    street = fields.Char(string='calle')
    calle = fields.Char(string='numero')
    interseccion = fields.Char(string='interseccion')
    provincia = fields.Char(string='provincia')
    celular = fields.Char(string='numero2')

