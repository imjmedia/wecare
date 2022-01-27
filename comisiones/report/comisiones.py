# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models


class ReporteComision(models.Model):
    _name = "comision.venta"
    _description = "Reporte de Comisiones de Venta"
    _auto = False


    date = fields.Datetime('Fecha de Último Pago', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Cliente', readonly=True)
    user_id = fields.Many2one('res.users', 'Vendedor', readonly=True)
    subtotal = fields.Float('Total sin Impuestos', readonly=True)
    comision = fields.Float('Comisión', readonly=True)
    invoice = fields.Many2one('account.move', string="Factura", readonly=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('posted', 'Publicado'),
        ('cancel', 'Cancelado')
    ], string='Status Factura', readonly=True)
    pricelist_id = fields.Char('Lista de Precio', readonly=True)
    days = fields.Integer('Días Vencidos', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'comision_venta')
        self.env.cr.execute("""
        CREATE or REPLACE VIEW comision_venta AS (
         SELECT row_number() OVER () AS id, line.date, line.partner_id, line.user_id,
         line.subtotal, line.comision, line.state, line.invoice, line.pricelist_id
         FROM( SELECT am.id as invoice, 
            CASE WHEN am.move_type = 'out_invoice' THEN am.fecha_ultimo_pago
            ELSE am.invoice_date
            END date, 
            am.partner_id as partner_id,
            am.invoice_user_id as user_id, CASE WHEN am.move_type = 'out_invoice' THEN am.amount_untaxed 
            ELSE -am.amount_untaxed END subtotal,
            CASE WHEN pp.type = 'vip' AND (am.invoice_date - fecha_factura) <= 30 AND am.move_type = 'out_invoice' THEN (am.amount_untaxed*0.015)
            WHEN pp.type = 'vip' AND (am.invoice_date - fecha_factura) <= 120 AND am.move_type = 'out_invoice' THEN (am.amount_untaxed*0.0125)
            WHEN pp.type = 'vip' AND (am.invoice_date - fecha_factura) > 120 AND am.move_type = 'out_invoice' THEN (am.amount_untaxed*0.00875)
            WHEN pp.type = 'final' AND (am.invoice_date - fecha_factura) <= 30 AND am.move_type = 'out_invoice' THEN (am.amount_untaxed*0.03)
            WHEN pp.type = 'final' AND (am.invoice_date - fecha_factura) <= 120 AND am.move_type = 'out_invoice' THEN (am.amount_untaxed*0.025)
            WHEN pp.type = 'final' AND (am.invoice_date - fecha_factura) > 120 AND am.move_type = 'out_invoice' THEN (am.amount_untaxed*0.0175)
            WHEN pp.type = 'mayoreo' AND (am.invoice_date - fecha_factura) <= 30 AND am.move_type = 'out_invoice' THEN (am.amount_untaxed*0.042)
            WHEN pp.type = 'mayoreo' AND (am.invoice_date - fecha_factura) <= 120 AND am.move_type = 'out_invoice' THEN (am.amount_untaxed*0.035)
            WHEN pp.type = 'mayoreo' AND (am.invoice_date - fecha_factura) > 120 AND am.move_type = 'out_invoice' THEN (am.amount_untaxed*0.0245)
            WHEN pp.type = 'vip' AND (am.invoice_date - fecha_factura) <= 30 AND am.move_type = 'out_refund' THEN (-am.amount_untaxed*0.015)
            WHEN pp.type = 'vip' AND (am.invoice_date - fecha_factura) <= 120 AND am.move_type = 'out_refund' THEN (-am.amount_untaxed*0.0125)
            WHEN pp.type = 'vip' AND (am.invoice_date - fecha_factura) > 120 AND am.move_type = 'out_refund' THEN (-am.amount_untaxed*0.00875)
            WHEN pp.type = 'final' AND (am.invoice_date - fecha_factura) <= 30 AND am.move_type = 'out_refund' THEN (-am.amount_untaxed*0.03)
            WHEN pp.type = 'final' AND (am.invoice_date - fecha_factura) <= 120 AND am.move_type = 'out_refund' THEN (-am.amount_untaxed*0.025)
            WHEN pp.type = 'final' AND (am.invoice_date - fecha_factura) > 120 AND am.move_type = 'out_refund' THEN (-am.amount_untaxed*0.0175)
            WHEN pp.type = 'mayoreo' AND (am.invoice_date - fecha_factura) <= 30 AND am.move_type = 'out_refund' THEN (-am.amount_untaxed*0.042)
            WHEN pp.type = 'mayoreo' AND (am.invoice_date - fecha_factura) <= 120 AND am.move_type = 'out_refund' THEN (-am.amount_untaxed*0.035)
            WHEN pp.type = 'mayoreo' AND (am.invoice_date - fecha_factura) > 120 AND am.move_type = 'out_refund' THEN (-am.amount_untaxed*0.0245)
            ELSE (am.amount_untaxed*0.0)
            END comision,
            am.state as state, am.move_type as type, rp.create_date, pp.type as pricelist_id,
            pp.name
            from public.account_move as am
            inner join public.res_partner as rp on rp.id = am.partner_id
            inner join (SELECT partner_id, MIN(invoice_date) as fecha_factura FROM public.account_move WHERE state = 'posted' GROUP BY partner_id) as fecha on fecha.partner_id = am.partner_id
            inner join public.ir_property as ip on rp.id = cast(substring(ip.res_id, strpos(ip.res_id, ',')+1, length(ip.res_id)) as integer)
            inner join public.product_pricelist as pp on pp.id = cast(substring(ip.value_reference, strpos(ip.value_reference, ',')+1, length(ip.value_reference)) as integer)
            where ip.name = 'property_product_pricelist' and am.move_type LIKE 'out%' and am.amount_residual = 0 
            ) as line
            WHERE
            line.state = 'posted'
         )""")