# -*- coding: utf-8 -*-

from odoo import fields, models,api, _

class VentaLinea(models.Model):
    _inherit = ['sale.order.line']

    x_units_per_uom = fields.Float(string="Unidades por Caja",compute="unidad_por_caja",store=True)
    x_price_per_unit = fields.Float(string="Precio por Pieza",compute="precio_por_pieza",store=True)

    @api.depends('product_uom')
    def unidad_por_caja(self):
        for record in self:
            uom_id = record.env.ref('uom.product_uom_unit')
            if record.product_uom and record.product_uom.category_id == uom_id.category_id:
                record['x_units_per_uom'] = record.product_uom._compute_quantity(1.0, uom_id)

    @api.depends('price_unit','x_units_per_uom')
    def precio_por_pieza(self):
        for record in self:
            if record['x_units_per_uom'] and record.price_unit:
                record['x_price_per_unit'] = record.price_unit / record['x_units_per_uom']
            else:
                record['x_price_per_unit'] = 0.0