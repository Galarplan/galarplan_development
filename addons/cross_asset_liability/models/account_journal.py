from odoo import _, api, fields, models

class AccountJournal(models.Model):
    _inherit  = 'account.journal'

    def _get_default_account_domain_two(self):
        return """[
            ('deprecated', '=', False),
            ('company_id', '=', company_id),
            ('account_type', 'not in', ('asset_receivable', 'liability_payable')),
            ('account_type', 'in', ('asset_cash', 'liability_credit_card', 'asset_current', 'liability_current') if type == 'bank'
                                   else ('asset_cash',) if type == 'cash'
                                   else ('income',) if type == 'sale'
                                   else ('expense',) if type == 'purchase'
                                   else ())
        ]"""

    
    
    default_account_id = fields.Many2one(
        comodel_name='account.account', check_company=True, copy=False, ondelete='restrict',
        string='Default Account',
        domain=_get_default_account_domain_two)
    


    

    # def _get_default_account_domain(self):
    #     # Llamar al método original para obtener el dominio base
    #     original_domain = super(AccountJournal, self)._get_default_account_domain()

    #     # Convertir el dominio original en una lista para modificarlo
    #     domain_list = eval(original_domain)

    #     # Buscar la condición 'account_type' en el dominio
    #     for index, condition in enumerate(domain_list):
    #         if condition[0] == 'account_type' and condition[1] == 'in' and self.type == 'bank':
    #             # Extender la lista de tipos de cuenta permitidos
    #             domain_list[index] = (
    #                 'account_type',
    #                 'in',
    #                 condition[2] + ('asset_current', 'liability_current')  # Agregar los nuevos tipos
    #             )

    #     # Retornar el dominio modificado
    #     return str(domain_list)