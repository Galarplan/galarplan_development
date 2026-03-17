from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import xlrd


MAPPING_TYPE = {
    # Mapeo directo (tipos que no cambiaron)
    'income': 'income',
    'equity': 'equity',
    'bank': 'asset_cash',
    'payable': 'liability_payable',
    'liability': 'liability_current',
    'asset': 'asset_current',
    'expense': 'expense',
    'view': 'view',
    'receivable': 'asset_receivable',  # Mejorado en v16
    'debtor': 'debtor',      # Alias en v8
    'creditor': 'creditor',       # Alias en v8
    'control': 'control',          # Tipo genérico en v16 (revisar caso por caso)
}

class LoadBudgetParent(models.TransientModel):
    _name = 'load.budget.relationship'
    _description = 'Wizard para cargar relaciones presupuestarias'
    
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
        required_fields = ['payable','payable_name','payable_type','account','account_name','account_type','codigo','gasto']
        for field in required_fields:
            if field not in headers:
                raise UserError(_(f"El archivo debe contener la columna {field}"))
        
        account = self.env['account.account']
        budget_group = self.env['budget.group']
        budget_accounting = self.env['budget.accounting']
        created_count = 0
        updated_count = 0
        
        # Procesar filas
        for row in range(1, sheet.nrows):
            row_data = {}
            for col in range(sheet.ncols):
                row_data[headers[col]] = sheet.cell_value(row, col)
            
            # Buscar grupo por código
            account_search = account.search([('code', '=', str(row_data.get('payable')))], limit=1)
            account_search2 = account.search([('code', '=', str(row_data.get('account')))], limit=1)


            self._cr.execute("""
                SELECT id 
                FROM account_account 
                WHERE company_id = %s and code = %s
            """, (self.company_id.id,row_data.get('payable')))

            result = self._cr.fetchall()

            self._cr.execute("""
                SELECT id 
                FROM account_account 
                WHERE company_id = %s and code = %s
            """, (self.company_id.id,row_data.get('account')))

            result2 = self._cr.fetchall()
            codigo_cp = 0
            codigo = 0
            
            if len(result):
                codigo_cp = result[0][0]
            else:
                codigo_cp = 0
            
            if len(result2):
                codigo = result2[0][0]
            else:
                codigo = 0

            account_search = 0 
            account_search2 = 0              
            code_search = budget_group.search([('code','=',str(row_data.get('codigo')))])
            print('======================',row_data.get('payable'),row_data.get('account'))
            print('======================',codigo_cp,codigo,code_search)
            if code_search:
                if codigo_cp == 0 :
                    account_search =account.create( {
                        'company_id': self.company_id.id,
                        'name': row_data.get('payable_name'),
                        'code': str(row_data.get('payable')),
                        'account_type': MAPPING_TYPE[row_data.get('payable_type')],
                        
                    })   
                
                if codigo == 0:
                    account_search2 = account.create( {
                        'company_id': self.company_id.id,
                        'name': row_data.get('account_name'),
                        'code': str(row_data.get('account')),
                        'account_type': MAPPING_TYPE[row_data.get('account_type')],
                        
                    })   
                
                
                search_relation = self.env['budget.accounting'].search([('account_cp_id','=',codigo_cp if codigo_cp != 0 else account_search.id),
                                                                        ('account_id','=',codigo if codigo != 0 else account_search2.id),
                                                                        ('budget_group_id','=',code_search.id)])
                print(account_search,account_search2,codigo_cp,codigo)
                if not search_relation:
                    
                    vals = {
                        'account_cp_id': codigo_cp if codigo_cp != 0 else account_search.id,
                        'account_id': codigo if codigo != 0 else account_search2.id,
                        'budget_group_id': code_search.id,
                        'is_expense_account': bool(row_data.get('gasto')),
                        'company_id': self.company_id.id,
                    }

                    print('===========================',vals)
                    budget_accounting.create(vals)
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
                'message': _(f"se actualizaron {updated_count} y se crearion {created_count}"),
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }