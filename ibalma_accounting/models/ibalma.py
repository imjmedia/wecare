# -*- coding: utf-8 -*-

from odoo import fields, models,api, _

class Cuenta(models.Model):
    _inherit = ['account.move']

    x_referencia_para_pago = fields.Char(string="Referencia para Pago",store=True)
    x_sale_order_id = fields.Many2one('sale.order',string="Pedido de Venta",compute="orden_venta",store=True,readonly=True)

    @api.depends('invoice_line_ids', 'invoice_line_ids.sale_line_ids', 'invoice_line_ids.sale_line_ids.order_id')
    def orden_venta(self):
        for inv in self:
            order = inv.mapped('invoice_line_ids.sale_line_ids.order_id')
            if order:
                inv['x_sale_order_id'] = order[0]
            else:
                inv['x_sale_order_id'] = False

class Pago(models.Model):
    _inherit = ['account.payment']

    x_num_operacion = fields.Char(string="Num Operacion",store=True)
    x_nombre_banco_ordext = fields.Char(string="Nombre Banco OrdExt")
    x_linea_cp = fields.Many2one('product.template',string="Linea CP",store=True)
    x_referencia_para_pago = fields.Char(string="Referencia para Pago",related="move_id.x_referencia_para_pago")
    x_sale_order_id = fields.Many2one(string="Sale Order",related="move_id.x_sale_order_id",readonly=True)


class Banco(models.Model):
    _inherit = ['account.bank.statement.line']

    x_sale_order_id = fields.Many2one(string="Sale Order", related="move_id.x_sale_order_id", readonly=True)
    x_referencia_para_pago = fields.Char(string="Referencia para Pago",related="move_id.x_referencia_para_pago")

class Contacto(models.Model):
    _inherit = ['res.partner']

    x_codigo_de_proveedor = fields.Char(string="Codigo de Proveedor",store=True)

class Venta(models.Model):
    _inherit = ['sale.order']

    x_codigo_de_proveedor = fields.Char(string="Codigo de Proveedor",related="partner_id.x_codigo_de_proveedor",store=True)

class Usuarios(models.Model):
    _inherit = ['res.users']

    x_codigo_de_proveedor = fields.Char(string="Codigo de Proveedor",related="partner_id.x_codigo_de_proveedor")
