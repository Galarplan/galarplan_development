# -*- coding: utf-8 -*-

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    x_is_seller = fields.Boolean(
        string='Es vendedor'
    )

    x_sales_active = fields.Boolean(
        string='Activo para ventas',
        default=True
    )

    x_is_jefe = fields.Boolean(
        string='Jefe de Grupo'
    )

    x_admin_crm = fields.Boolean(
        string='Administrador CRM'
    )

