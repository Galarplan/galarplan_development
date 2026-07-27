# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class AccountSavingPlan(models.Model):
    _name = 'account.saving.plan.type'
    _description = 'Estados de Plan de Ahorro'
    _order = 'sequence, name'
    
    name = fields.Char(string='Nombre', required=True, translate=True)
    code = fields.Char(string='Código', required=True)
    sequence = fields.Integer(string='Secuencia', default=10)
    active = fields.Boolean(string='Activo', default=True)
    description = fields.Text(string='Descripción')
    color = fields.Integer(string='Color', default=0)


    # @api.model
    # def _load_default_states(self):
    #     """Carga los estados por defecto desde account.saving"""
    #     states = [
    #         ('draft', 'Borrador'),
    #         ('posted', 'Publicado'),
    #         ('active', 'Activo'),
    #         ('adjudicated_with_assets', 'Adjudicado con Bien'),
    #         ('adjudicated_without_assets', 'Adjudicado sin Bien'),
    #         ('awarded', 'Adjudicado'),
    #         ('pending_authorizated', 'Autorización de Retiro Pendiente'),
    #         ('anulled', 'Anulado'),
    #         ('disabled', 'Desactivado'),
    #         ('retired', 'Retirado'),
    #         ('precanceled', 'Pre-Cancelado'),
    #         ('estructured', 'Re-estructurado'),
    #         ('cancelled', 'Cancelado'),
    #         ('moved', 'Traspaso'),
    #         ('closed', 'Cerrado'),
    #     ]
    #     for code, name in states:
    #         if not self.search([('code', '=', code)]):
    #             self.create({
    #                 'code': code,
    #                 'name': name,
    #             })
    
    # @api.model
    # def get_selection_states(self):
    #     """Retorna los estados como lista de tuplas para usar en Selection"""
    #     states = self.search([])
    #     return [(state.code, state.name) for state in states]