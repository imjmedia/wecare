# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner_corp_id=fields.Many2one('res.partner', string='Corportive Company', index=True)