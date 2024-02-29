# -*- coding: utf-8 -*-

from odoo import fields, models,api


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'


    quitar_chars_especial = fields.Boolean('Quitar Chars Especiales', default=False, help='Elimina guiones y similares del nombre de la factura (para chedraui)')