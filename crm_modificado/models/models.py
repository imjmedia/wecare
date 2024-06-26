# -*- coding: utf-8 -*-

from odoo import models, fields, api

class crmModificado(models.Model):
    _inherit = 'crm.lead'

    @api.depends('quotation_count', 'sale_amount_total')
    def sacar_ingreso(self):
        self.expected_revenue = 0.0
        x = 0
        for record in self:
            vendido = self.env['sale.order'].search(
                [('opportunity_id', '=', record.id), ('state', '!=', 'sale'), ('state', '!=', 'cancel')])
            if record.quotation_count == 0:
                if record.sale_amount_total:
                    record.expected_revenue = record.sale_amount_total
                else:
                    record.expected_revenue = 0.0
            elif record.quotation_count != 0:
                if record.sale_amount_total:
                    record.expected_revenue = record.sale_amount_total
                else:
                    for venta in vendido:
                        if x == 0:
                            record.expected_revenue = venta.amount_untaxed
                        x = x + 1
            else:
                record.expected_revenue = 0.0

    expected_revenue = fields.Monetary('Expected Revenue', currency_field='company_currency', tracking=True,compute="sacar_ingreso",store=True)

