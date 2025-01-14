# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
import re
import unicodedata
import base64
import io
import csv
from datetime import datetime

class HrEmployeePayment(models.Model):
    _name = "hr.employee.payment"
    _description = "Pagos a Empleados"

    @api.model
    def _get_default_company_id(self):
        if self._context.get("allowed_company_ids", []):
            return self._context.get("allowed_company_ids", [])[0]
        return False

    name = fields.Char("Descripción", size=255, required=True)
    company_id = fields.Many2one(
        "res.company",
        string="Compañia",
        required=True,
        copy=False,
        default=lambda self: self.env.company,
    )

    currency_id = fields.Many2one("res.currency", "Moneda", compute="compute_company_values", store=True)
    partner_id = fields.Many2one("res.partner", "Contacto", compute="compute_company_values", store=True)

    date_process = fields.Date("Fecha del Proceso", default=fields.Date.today(), required=True)

    month_id = fields.Many2one("calendar.month", "Mes", compute="_compute_date_info", store=True, required=False)
    year = fields.Integer("Año", compute="_compute_date_info", store=True, required=False)

    comments = fields.Text("Comentarios")

    total = fields.Monetary("Total", digits=(16, 2), default=0.00, compute="_compute_total", store=True, required=False)
    state = fields.Selection([('draft', 'Preliminar'),
                              ('approved', 'Aprobado'),
                              ('cancelled', 'Anulado') ], default="draft", required=True, string="Estado")

    payment_bank_account_id=fields.Many2one("res.partner.bank","# Cuenta Bancaria",required=False)
    payment_journal_id = fields.Many2one("account.journal", "Diario", required=True)

    movement_ids = fields.Many2many("hr.employee.movement", "payment_movement_rel","payment_id","movement_id","Movimientos")
    payslip_ids = fields.Many2many("hr.payslip.run", "payment_payslip_run_rel", "payment_id", "payslip_run_id","Roles")

    line_ids=fields.One2many("hr.employee.payment.line","process_id","Detalle de Pagos")
    move_ids=fields.One2many("hr.employee.payment.move","process_id","Asiento Contable")
    move_id = fields.Many2one("account.move", string="# Asiento")

    csv_export_file =fields.Binary(string="Archivo Reporte")
    csv_export_filename = fields.Char(stirng="Nombre Archivo")

    attachment_id=fields.Many2one("ir.attachment","Informe Adjunto")

    _rec_name = "name"#
    _order = "id desc"

    _check_company_auto = True

    @api.depends('company_id')
    def compute_company_values(self):
        for brw_each in self:
            brw_each.currency_id = brw_each.company_id and brw_each.company_id.currency_id.id or False
            brw_each.partner_id = brw_each.company_id and brw_each.company_id.partner_id.id or False

    @api.onchange('company_id')
    def onchange_company_id(self):
        self.compute_company_values()
        self.payment_bank_account_id=False
        self.payment_journal_id=False
        self.movement_ids=[(6,0,[])]
        self.payslip_ids = [(6, 0, [])]
        self.line_ids = [(5,)]
        self.move_ids = [(5,)]

    @api.depends('line_ids')
    @api.onchange('line_ids')
    def _compute_total(self):
        DEC=2
        for brw_each in self:
            total=0.00
            for brw_line in brw_each.line_ids:
                total+=brw_line.total
            brw_each.total=round(total,DEC)

    @api.onchange('movement_ids','payslip_ids','payment_journal_id')
    @api.depends('movement_ids', 'payslip_ids','payment_journal_id')
    def onchange_lines(self):
        for brw_each in self:
            line_ids = [(5,)]
            movement_ids=brw_each.movement_ids.ids+[-1,-1]
            payslip_ids = brw_each.payslip_ids.ids+[-1,-1]
            self._cr.execute("""select heml.employee_id,
heml.name,
heml.bank_history_id as bank_id,
heml.bank_acc_number,
heml.bank_tipo_cuenta,
heml.bank_account_id ,
heml.total
from hr_employee_movement hem
inner join hr_employee_movement_line heml on heml.process_id=hem.id 
inner join hr_salary_rule hsr on hsr.id=hem.rule_id 
where hsr.payment=true and hem.id in %s and hem.state='approved'
union
select ps.employee_id,
ps.name,
ps.bank_history_id  as bank_id,
ps.bank_acc_number ,
ps.bank_tipo_cuenta,
ps.bank_account_id ,
ps.total_payslip as total
from hr_payslip_run psr
inner join hr_payslip ps on ps.payslip_run_id=psr.id
where psr.id in %s and psr.state='close'""",(tuple(movement_ids),tuple(payslip_ids)))
            result=self._cr.dictfetchall()
            if result:
                for each_result in result:
                    line_ids.append((0,0,each_result))
            move_ids=[(5,)]
            total=0.00
            for brw_document in brw_each.movement_ids:
                if brw_document.legal_iess and  brw_document.move_id:
                    for brw_line in brw_document.move_id.line_ids:
                        if brw_line.credit > 0:  ##valores a pagar
                            move_ids += [(0, 0, {
                                "account_id": brw_line.account_id.id,
                                "move_id": brw_document.move_id.id,
                                "debit": brw_line.credit,
                                "credit": 0,
                                "move_line_id":brw_line.id,
                                "partner_id":brw_document.company_id.partner_id.id
                            })]
                            total+=brw_line.credit
                if not brw_document.legal_iess and  brw_document.move_id:
                    for brw_line in brw_document.move_id.line_ids:
                        if brw_line.credit > 0:  ##valores a pagar
                            move_ids += [(0, 0, {
                                "account_id": brw_line.account_id.id,
                                "move_id": brw_document.move_id.id,
                                "debit": brw_line.credit,
                                "credit": 0,
                                "move_line_id":brw_line.id,
                                "partner_id":brw_document.company_id.partner_id.id
                            })]
                            total+=brw_line.credit
            ######################
            brw_company=brw_each.company_id
            ACCOUNT=self.env.ref('gps_hr.rule_SALARIO').rule_account_ids.filtered(lambda x:  x.type=='payslip' and  x.account_type=='credit' and  x.company_id==brw_company).mapped('account_id')
            for brw_document in brw_each.payslip_ids:
                if brw_document.legal_iess and brw_document.move_id:
                    for brw_line in brw_document.move_id.line_ids:
                        if brw_line.credit > 0 and brw_line.account_id==ACCOUNT:  ##valores a pagar
                            move_ids += [(0, 0, {
                                "account_id": brw_line.account_id.id,
                                "move_id": brw_document.move_id.id,
                                "debit": brw_line.credit,
                                "credit": 0,
                                "move_line_id":brw_line.id,
                                "partner_id":brw_document.company_id.partner_id.id
                            })]
                            total+=brw_line.credit
                if not brw_document.legal_iess:
                    for brw_slip in brw_document.slip_ids:
                        for brw_invoice in brw_slip.invoice_ids:
                            move_ids += [(0, 0, {
                                    "account_id": brw_invoice.partner_id.property_account_payable_id.id,
                                    "move_id": brw_invoice.id,
                                    "debit": brw_invoice.amount_residual,
                                    "credit": 0,
                                    "move_line_id":False,
                                    "partner_id":brw_invoice.partner_id.id
                            })]
                            total+=brw_invoice.amount_residual
            acc_id = brw_each.payment_journal_id.default_account_id.id
            if total:
                move_ids += [(0, 0, {
                    "account_id": acc_id,
                    "move_id": False,
                    "debit": 0,
                    "credit": total,
                    "partner_id": brw_each.company_id.partner_id.id
                })]
            brw_each.line_ids=line_ids
            brw_each.move_ids = move_ids

    def quitar_tildes(texto):
        # Normalizar el texto a su forma descompuesta
        texto_normalizado = unicodedata.normalize('NFD', texto)
        # Eliminar los caracteres diacríticos (tildes, ñ, etc.)
        texto_sin_tildes = ''.join(
            char for char in texto_normalizado if unicodedata.category(char) != 'Mn'
        )
        return texto_sin_tildes
    
    def genera_archivo(self):
        print('genera archivo')
        company = self.company_id.name
        if company == 'IMPORT GREEN POWER TECHNOLOGY, EQUIPMENT & MACHINERY ITEM S.A':
            codbanco = '11074'  # Verificar!
        if company == 'GREEN ENERGY CONSTRUCTIONS & INTEGRATION C&I SA':
            codbanco = '11100'  # Verificar!
        csvfile = io.StringIO()
        writer = csv.writer(csvfile, delimiter='\t', quoting=csv.QUOTE_NONE, escapechar='')
        fechahoy = datetime.now()
        i = 1
        file_name =False
        journal_name=self.payment_journal_id.name.lower()
        if 'bolivariano' in journal_name:
            file_name='pago_nomina.biz'
        if 'internacional' in journal_name:
            file_name='pago_nomina.txt'
        for x in self.line_ids:
            identificacion = x.employee_id.identification_id
            tipo_identificacion = (x.employee_id.l10n_latam_identification_type_id == self.env.ref(
                "l10n_ec.ec_dni")) and 'C' or 'P'
            nombre_persona_pago = x.employee_id.name
            if x.employee_id.tercero:
                identificacion = x.employee_id.identificacion_tercero
                tipo_identificacion = (x.employee_id.l10n_latam_identification_tercero_id == self.env.ref(
                    "l10n_ec.ec_dni")) and 'C' or 'P'
                if (x.employee_id.l10n_latam_identification_tercero_id == self.env.ref(
                    "l10n_ec.ec_ruc")):
                    tipo_identificacion='R'
                nombre_persona_pago = x.employee_id.nombre_tercero or nombre_persona_pago
            if 'bolivariano' in journal_name:
                tipo_cta = '03' if x.employee_id.bank_type == 'checking' else '04'
                forma_pago = 'CUE' if str(x.employee_id.bank_id.bic)== '37' else 'COB'
                code_bank = '34' if str(x.employee_id.bank_id.bic) == '37' else str(x.employee_id.bank_id.bic)
                # pname = re.sub(r'[^0-9]', '', row_data['payment_name'].replace('.', ''))
                idpago = self.id
                fila = (
                        'BZDET' + str(i).zfill(6) +  # 001-011
                        identificacion.ljust(18) +  # 012-029
                        tipo_identificacion+#x.employee_id.partner_id.l10n_latam_identification_type_id.name[:1].upper()+# if x.employee_id.partner_id.l10n_latam_identification_type_id else '' +  # 030-030
                        identificacion.ljust(14) +  # 031-044
                        nombre_persona_pago[:60].ljust(60).replace("Ñ", "N").replace("ñ", "n") +  # 045-104
                        forma_pago[:3] +  # 105-107
                        '001' +  # Código de país (001) 108-110
                        #code_bank[:2].ljust(2) +  # 111-112
                        ' ' * 2+ # 111-112
                        tipo_cta +  # 113-114
                        x.employee_id.account_number[:20].ljust(20) +  # 115-134
                        '1' +  # Código de moneda (1) 135-135
                        str("{:.2f}".format(x.total)).replace('.', '').zfill(15) +  # 136-150
                        x.name[:60].ljust(60) +  # 151-210
                        #(row_data['payment_name']).zfill(14) +  # 211-225
                        str(idpago).zfill(15) +  # 211-225
                        '0' * 15 +  # Número de comprobante de retención 226-240
                        '0' * 15 +  # Número de comprobante de IVA 241-255
                        '0' * 20 +  # Número de factura - SRI 256-275
                        ' ' * 9 +  # Código de grupo 276-285
                        ' ' * 50 +  # Descripción del grupo 286-335
                        ('NO TIENE').ljust(50) + #x.employee_id.partner_id.street[:50].ljust(50)  if x.employee_id.partner_id.street else 'NO TIENE'+  # Dirección del beneficiario 336-385
                        ' ' * 21 +  # Teléfono 386-405
                        'RPA' +  # Código del servicio 406-408
                        ' ' * 10 * 3 +  # Cédula 1, 2, 3 para retiro 409-438
                        ' ' +  # Seña de control de horario 439-439
                        codbanco +  # Código empresa asignado 440-444
                        '0' +  # Código de sub-empresa 445-450
                        codbanco +  # Código de sub-empresa 445-450
                        'RPA' + #code_bank[:2].ljust(2) +  # Sub-motivo de pago/cobro 451-453
                        ' ' * 10 + 
                        code_bank[:2].ljust(2)
                        )
                print(fila)
                writer.writerow([fila])
                i = i + 1
            if 'internacional' in journal_name:
                tipo_cta = 'CTE' if x.employee_id.bank_type == 'checking' else 'AHO'
                # code_bank = 'CUE001'.ljust(8) if row_data['bank_code'] == '37' else 'COB001'.ljust(8)
                forma_pago = 'CUE' if str(x.employee_id.bank_id.bic) == '37' else 'COB'
                code_bank = str(x.employee_id.bank_id.bic)
                payment_name=x.name[:60].ljust(60)
                pname = re.sub(r'[^0-9]', '',payment_name.replace('.', ''))
                codpago = re.sub(r'[^0-9]', '', pname)
                fila = [
                    'PA',
                    identificacion,
                    'USD',
                    str("{:.2f}".format(x.total)).replace('.', ''),
                    'CTA',
                    tipo_cta,
                    x.employee_id.account_number,
                    payment_name,
                    tipo_identificacion,
                    identificacion,
                    nombre_persona_pago,
                    code_bank
                ]
                writer.writerow(fila)
        file_content = csvfile.getvalue()
        if not file_name:
            raise ValidationError(_("No hay nombre definido para el archivo"))
        if not file_content.strip():
            raise UserError(_("El archivo generado está vacío. Por favor, revise los datos de entrada."))
        file_content_base64 = base64.b64encode(file_content.encode())
        self.csv_export_file = file_content_base64
        self.csv_export_filename = file_name#
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create({'name': f"{file_name}",
                                            'type': "binary",
                                            'datas': file_content_base64,
                                            'mimetype': 'text/csv',
                                            'store_fname': file_name})
        self.attachment_id = attachment_id.id
        download_url = '/web/content/' + str(attachment_id.id) + '?download=true'
        return {
            "type": "ir.actions.act_url",
            "url": str(base_url) + str(download_url),
            "target": "new",
        }

    @api.onchange('date_process')
    def onchange_account_date_process(self):
        self.update_date_info()

    @api.depends('date_process')
    def _compute_date_info(self):
        for brw_each in self:
            brw_each.update_date_info()

    def update_date_info(self):
        for brw_each in self:
            month_id = False
            year = False
            if brw_each.date_process:
                month_srch = self.env["calendar.month"].sudo().search([('value', '=', brw_each.date_process.month)])
                year = brw_each.date_process.year
                month_id = month_srch and month_srch[0].id or False
            brw_each.month_id = month_id
            brw_each.year = year

    def unlink(self):
        for brw_each in self:
            if self._context.get("validate_unlink", True):
                if brw_each.state != 'draft':
                    raise ValidationError(_("No puedes borrar un registro que no sea preliminar"))
        return super(HrEmployeePayment, self).unlink()

    def action_approved(self):
        OBJ_MOVE = self.env["account.move"]
        for brw_each in self:
            if not brw_each.move_ids:
                raise ValidationError(_("No existen listas para generar el asiento contable"))
            vals = {
                    "move_type": "entry",
                    "name": "/",
                    'narration': brw_each.name,
                    'date': brw_each.date_process,
                    'ref': "PAGO DE NOMINA # %s" % (brw_each.id,),
                    'company_id': brw_each.company_id.id,
                    'journal_id': brw_each.payment_journal_id.id,
            }
            line_ids=[(5,)]
            for brw_line in brw_each.move_ids:
                line_ids += [(0, 0, {
                        "name": brw_each.name,
                        'credit': brw_line.credit,
                        'debit': brw_line.debit,
                        'ref': brw_each.name,
                        'account_id': brw_line.account_id.id,
                        'partner_id': brw_each.partner_id and brw_each.partner_id.id or False,
                        'date': brw_each.date_process,
                        "movement_payment_id":brw_line.id
                    })]
            vals["line_ids"] = line_ids
            brw_move = OBJ_MOVE.create(vals)
            brw_move.action_post()
            if brw_move.state != "posted":
                raise ValidationError(
                        _("Asiento contable %s,id %s no fue publicado!") % (brw_move.name, brw_move.id))
            brw_invoice_lines = self.env["account.move.line"]
            for x in brw_move.line_ids:
                if x.debit > 0 and x.amount_residual != 0.00:
                    brw_invoice_lines+=x
                    for brw_movement in brw_each.movement_ids:
                        for y in brw_movement.move_id.line_ids:
                            if y.credit > 0 and y.account_id == x.account_id and y.amount_residual != 0.00:
                                brw_invoice_lines += y
                    #####
                    for brw_payslip in brw_each.payslip_ids:
                        for y in brw_payslip.move_id.line_ids:
                            if y.credit > 0 and y.account_id == x.account_id and y.amount_residual != 0.00:
                                brw_invoice_lines += y

                    if len(brw_invoice_lines) <= 1:
                        raise ValidationError(_("No hay nada que reconciliar para %s documento %s") % (brw_each.name,))
                    brw_invoice_lines.reconcile()

            for brw_document in brw_each.movement_ids:
                brw_document.action_paid()
            for brw_document in brw_each.payslip_ids:
                brw_document.action_paid()
            brw_each.write({"move_id":brw_move.id,
                            "state":"approved"
                            })
        return True
