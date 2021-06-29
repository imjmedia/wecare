# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api,_
from odoo.exceptions import UserError

class account_invoice_line(models.Model):
    _inherit ='account.move.line'

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.move_id.manual_currency_rate_active:
            self = self.with_context(override_currency_rate=self.move_id.manual_currency_rate)
        return super(account_invoice_line, self)._onchange_product_id()

class account_invoice(models.Model):
    _inherit ='account.move'

    @api.onchange('tipo_de_cambio')
    def cambio(self):
        self.manual_currency_rate = 0
        if self.tipo_de_cambio:
            self.manual_currency_rate = (1/self.tipo_de_cambio)

    manual_currency_rate_active = fields.Boolean('¿Tipo de Cambio Manual?', store=True)
    manual_currency_rate = fields.Float('Tarifa', digits=(12,9), compute="cambio", default=0.0)
    tipo_de_cambio = fields.Float(string="Tipo de Cambio", digits=(12, 2), default=0.0)

    def action_move_create(self):
        """ Creates invoice related analytics and financial move lines """
        if self.manual_currency_rate_active:
            self = self.with_context(override_currency_rate=self.manual_currency_rate)
        return super(account_invoice, self).action_move_create()







# # vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
