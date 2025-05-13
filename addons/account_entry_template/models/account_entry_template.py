from odoo import _, api, fields, models



class AccountEntryTemplate(models.Model):
    _name = 'account.entry.template'
    _description = 'Plantilla de Asientos Contables'

    name = fields.Char(string="Nombre de la Plantilla", required=True)
    journal_id = fields.Many2one('account.journal', string="Diario", required=True)
    company_id = fields.Many2one('res.company', default = lambda self: self.env.company.id)
    code = fields.Char('Code')
    line_ids = fields.One2many('account.entry.template.line', 'template_id', string="Líneas de la Plantilla")

    def action_create_entries(self, number=1):
        move_obj = self.env['account.move']
        last_move = None
        for _ in range(number):
            
            move_vals = {
                'journal_id': self.journal_id.id,
                'ref': self.name,
                'line_ids': [],
                'company_id': self.company_id.id,
            }

            lines = []
            for line in self.line_ids:
                account_id = line.account_template.id if line.account_template else False
                if not account_id:
                    continue
                    
                line_vals = {
                    'account_id': account_id,
                    'name': line.product_id.name if line.product_id else '/',
                    'debit': 0.0,
                    'credit': 0.0,
                    'product_id': line.product_id.id if line.product_id else False,
                    'display_type': line.display_type,
                    # 'budget_item_rel': line.budget_line_id.id if line.budget_line_id else False,
                }
                
                lines.append((0, 0, line_vals))
                
            move_vals['line_ids'] = lines
            last_move = move_obj.create(move_vals)

        # Si se creó solo uno, mostrarlo
        if number == 1 and last_move:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Recaudaciones',
                'res_model': 'account.move',
                'view_mode': 'form',
                'res_id': last_move.id,
                'target': 'current',
                'context': {'default_company_id': self.company_id.id},
            }



class AccountEntryTemplateLine(models.Model):
    _name = 'account.entry.template.line'
    _description = 'Línea de Plantilla de Asiento Contable'

    template_id = fields.Many2one('account.entry.template', string="Plantilla")
    product_id = fields.Many2one('product.product', string="Producto")
    account_template = fields.Many2one('account.account', string="Cuenta")
    # debit_account_id = fields.Many2one('account.account', string="Cuenta al Debe")
    # credit_account_id = fields.Many2one('account.account', string="Cuenta al Haber")
    # budget_line_id = fields.Many2one('budget.transaction.line', string="Partida Presupuestaria")
    debit_bol = fields.Boolean('Ubicado en el Debe?',default = False)
    display_type = fields.Selection(
        selection=[
            ('product', 'Product'),
            ('cogs', 'Cost of Goods Sold'),
            ('tax', 'Tax'),
            ('rounding', "Rounding"),
            ('payment_term', 'Payment Term'),
            ('line_section', 'Section'),
            ('line_note', 'Note'),
            ('epd', 'Early Payment Discount')
        ],
        required=True,
    )
    # amount = fields.Monetary(string="Monto")
    # currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id.id)
