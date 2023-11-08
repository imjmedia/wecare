# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    dont_calculate = fields.Boolean(string='Dont Calculate Commission')
    net_margin = fields.Float('Net Margin')
    gross_margin = fields.Float('Net profit')
    net_margin_por = fields.Float('Net Margin profit')
