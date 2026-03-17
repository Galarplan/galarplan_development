from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import xlrd

# MAPPING_TYPE = {
#     # Mapeo directo (tipos que no cambiaron)
#     'income': 'income',
#     'equity': 'equity',
#     'bank': 'asset_cash',
#     'payable': 'liability_payable',
#     'liability': 'liability_current',
#     'asset': 'asset_current',
#     'expense': 'expense',
#     'view': 'view',
#     'receivable': 'asset_receivable',  # Mejorado en v16
#     'debtor': 'debtor',      # Alias en v8
#     'creditor': 'creditor',       # Alias en v8
#     'control': 'control',          # Tipo genérico en v16 (revisar caso por caso)
# }


# Constante con el mapeo de cuentas contables
MAPPING_TYPE = {
    "Por cobrar": "asset_receivable",
    "Banco y efectivo": "asset_cash",
    "Activos corrientes": "asset_current",
    "Activos no corrientes": "asset_non_current",
    "Prepagos": "asset_prepayments",
    "Activos fijos": "asset_fixed",
    "Por pagar": "liability_payable",
    "Tarjeta de Crédito": "liability_credit_card",
    "Pasivos corrientes": "liability_current",
    "Pasivos no corrientes": "liability_non_current",
    "Capital neto": "equity",
    "Ganancias del año actual": "equity_unaffected",
    "Ingreso": "income",
    "Inventario": "asset_warehouse",
    "Otros Activos Corrientes": "asset_other_current",
    "Otros Pasivos Corrientes": "liability_other_current",
    "Otros Ingresos": "income_other",
    "Expensas": "expense",
    "Depreciation": "expense_depreciation",
    "Cost of Revenue": "expense_direct_cost",
    "Off-Balance Sheet": "off_balance",
    "Otros Gastos": "expense_other",
    "View": "view"
}

class LoadBudgetParent(models.TransientModel):
    _name = 'load.accounts'
    _description = 'Wizard para cargar cuentas contables'
    
    company_id = fields.Many2one('res.company', default =  lambda self: self.env.company.id)
    file = fields.Binary('Archivo Excel', required=True)
    filename = fields.Char('Nombre del archivo')
    update_existing = fields.Boolean('Actualizar registros existentes', default=True)
    
    def action_import(self):
        self.ensure_one()
        if not self.file:
            raise UserError(_("Por favor sube un archivo Excel"))
        
        try:
            file_content = base64.b64decode(self.file)
            book = xlrd.open_workbook(file_contents=file_content)
            sheet = book.sheet_by_index(0)
        except:
            raise UserError(_("El archivo no es un Excel válido"))
        
        # Obtener encabezados
        headers = []
        for col in range(sheet.ncols):
            headers.append(sheet.cell_value(0, col).lower().strip())
        
        # Validar estructura del archivo
        required_fields = ['code', 'name_account', 'type']
        for field in required_fields:
            if field not in headers:
                raise UserError(_(f"El archivo debe contener la columna {field}"))
        
        account = self.env['account.account']
        created_count = 0
        updated_count = 0
        
        # Procesar filas
        for row in range(1, sheet.nrows):
            row_data = {}
            for col in range(sheet.ncols):
                row_data[headers[col]] = sheet.cell_value(row, col)
            
            # Buscar grupo por código
            # account_search = account.search([('code', '=', str(row_data.get('code')))], limit=1)

            self._cr.execute("""
                SELECT id 
                FROM account_account 
                WHERE company_id = %s and code = %s
            """, (self.company_id.id,row_data.get('code')))

            result = self._cr.fetchall()

            if len(result):
                codigo_cp = result[0][0]

                account_search = self.env['account.account'].browse(codigo_cp)
                
                account_search.write({'name':str(row_data.get('name_account'))})
                updated_count += 1
            else:

                # Preparar datos
                vals = {
                    'company_id': self.company_id.id,
                    'name': row_data.get('name_account'),
                    'code': str(row_data.get('code')),
                    'account_type': MAPPING_TYPE[row_data.get('type')],
                }
                # print('=========================',vals)
                account.create(vals)
                created_count += 1



        #     # Manejar jerarquía
        #     parent_code = str(row_data.get('parent_code', '')) or str(row_data.get('code_parent', ''))
        #     if parent_code and len(parent_code) < len(vals['code']):
        #         parent = BudgetGroup.search([('code', '=', parent_code)], limit=1)
        #         if parent:
        #             vals['parent_id'] = parent.id
            
        #     if group:
        #         if self.update_existing:
        #             group.write(vals)
        #             updated_count += 1
        #     else:
        #         BudgetGroup.create(vals)
        #         created_count += 1
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Importación completada'),
                'message': _(f"se actualizaron {updated_count} y se crearon {created_count}"),
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }