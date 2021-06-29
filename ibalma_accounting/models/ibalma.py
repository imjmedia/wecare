# -*- coding: utf-8 -*-

from odoo import fields, models,api, _

class Cuenta(models.Model):
    _inherit = ['account.move']

    x_referencia_para_pago = fields.Char(string="Referencia para Pago",store=True)

class Pago(models.Model):
    _inherit = ['account.payment']

    x_num_operacion = fields.Char(string="Num Operacion",store=True)
    x_nombre_banco_ordext = fields.Char(string="Nombre Banco OrdExt")
    x_linea_cp = fields.Many2one('product.template',string="Linea CP",store=True)
    x_referencia_para_pago = fields.Char(string="Referencia para Pago",related="move_id.x_referencia_para_pago")

class Banco(models.Model):
    _inherit = ['account.bank.statement.line']

    x_referencia_para_pago = fields.Char(string="Referencia para Pago",related="move_id.x_referencia_para_pago")
