# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api,_
from odoo.exceptions import UserError

class account_invoice_line(models.Model):
    _inherit ='account.move.line'

    # #@api.model
    # def _get_fields_onchange_subtotal_model(self, price_subtotal, move_type, currency, company, date):
    #     ''' This method is used to recompute the values of 'amount_currency', 'debit', 'credit' due to a change made
    #     in some business fields (affecting the 'price_subtotal' field).
    #
    #     :param price_subtotal:  The untaxed amount.
    #     :param move_type:       The type of the move.
    #     :param currency:        The line's currency.
    #     :param company:         The move's company.
    #     :param date:            The move's date.
    #     :return:                A dictionary containing 'debit', 'credit', 'amount_currency'.
    #     '''
    #     if move_type in self.move_id.get_outbound_types():
    #         sign = 1
    #     elif move_type in self.move_id.get_inbound_types():
    #         sign = -1
    #     else:
    #         sign = 1
    #     # balance = 0
    #     amount_currency = price_subtotal * sign
    #     move_ids = self.env['account.move'].search([], limit=1, order="id desc")
    #     if move_ids.manual_currency_rate_active:
    #         balance = amount_currency
    #         return {
    #             'amount_currency': amount_currency,
    #             'currency_id': currency.id,
    #             'debit': balance > 0.0 and balance or 0.0,
    #             'credit': balance < 0.0 and -balance or 0.0,
    #         }
    #     else:
    #         balance = currency._convert(amount_currency, company.currency_id, company,
    #                                     date or fields.Date.context_today(self))
    #         return {
    #             'amount_currency': amount_currency,
    #             'currency_id': currency.id,
    #             'debit': balance > 0.0 and balance or 0.0,
    #             'credit': balance < 0.0 and -balance or 0.0,
    #         }

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







# # vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
