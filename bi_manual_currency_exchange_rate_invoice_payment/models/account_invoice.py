# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools.misc import formatLang, format_date


class account_invoice(models.Model):
    _inherit ='account.move'

    @api.onchange('tipo_de_cambio')
    def cambio(self):
        self.manual_currency_rate = 0
        if self.tipo_de_cambio:
            self.manual_currency_rate = (1/self.tipo_de_cambio)

    manual_currency_rate_active = fields.Boolean('Apply Manual Exchange')
    manual_currency_rate = fields.Float('Tarifa', digits=(12,6), compute="cambio", default=0.0)
    tipo_de_cambio = fields.Float(string="Tipo de Cambio", digits=(12, 4), default=0.0)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _get_default_line_name(self, document, amount, currency, date, partner=None):
        ''' Helper to construct a default label to set on journal items.
        Se restaura de versión 15
        E.g. Vendor Reimbursement $ 1,555.00 - Azure Interior - 05/14/2020.

        :param document:    A string representing the type of the document.
        :param amount:      The document's amount.
        :param currency:    The document's currency.
        :param date:        The document's date.
        :param partner:     The optional partner.
        :return:            A string.
        '''
        values = ['%s %s' % (document, formatLang(self.env, amount, currency_obj=currency))]
        if partner:
            values.append(partner.display_name)
        values.append(format_date(self.env, fields.Date.to_string(date)))
        return ' - '.join(values)



# # vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
