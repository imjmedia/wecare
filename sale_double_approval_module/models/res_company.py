# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class CompanySaleInherit(models.Model):
    _inherit = 'res.company'

    so_double_validation = fields.Boolean("Sale Order Approval",default=True)

    so_double_validation_amount = fields.Monetary(string='SO Double validation amount', default=1.0,
        help="SO Minimum amount for which a validation is required")