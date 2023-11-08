# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class SmartCommission(models.Model):
    _inherit = 'res.users'

    commission_user_rate = fields.Integer(string='Commission', default=0)
