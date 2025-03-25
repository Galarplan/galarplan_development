# -*- coding: utf-8 -*-
from odoo import models, fields, api


class daily_session_hours_history(models.Model):
    _name = 'daily.session.hours.history'
    _description = 'Control de Sesiones Diaria por Modulo'
