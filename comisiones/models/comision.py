# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Comision(models.Model):
    _inherit = ['product.pricelist']


    type = fields.Selection([('vip','VIP'),('mayoreo','Mayoreo'),('final','Cliente Final')],string='Tipo de Lista', store=True)

    