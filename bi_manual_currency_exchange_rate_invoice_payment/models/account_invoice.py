# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools.misc import formatLang, format_date, get_lang

import json

class account_invoice(models.Model):
    _inherit ='account.move'

    @api.onchange('tipo_de_cambio')
    def cambio(self):
        self.manual_currency_rate = 0
        if self.tipo_de_cambio:
            self.manual_currency_rate = (1/self.tipo_de_cambio)

    manual_currency_rate_active = fields.Boolean('Apply Manual Exchange')
    manual_currency_rate = fields.Float('Tarifa', digits=(12,6), compute="cambio", default=0.0)
    tipo_de_cambio = fields.Float(string="Tipo de Cambio", digits=(12, 6), default=0.0)


# # vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
