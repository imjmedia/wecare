# -*- coding: utf-8 -*-


import time
from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, format_datetime

class pago_venta(models.Model):
    _inherit = 'sale.order'

    @api.depends_context('facturado')
    def pagofactura(self):
        self.pago = False
        x = 2
        facturado = self.env['account.move'].search(
            [('invoice_origin', '=', self.name), ('state', '=', 'posted')])
        if facturado == False:
            self.pago = False
        else:
            for factura in facturado:
                x = factura.amount_residual
            if x == 0:
                self.pago = True
            else:
                self.pago = False

    pago = fields.Boolean(string="¿Pago Generado?",compute='pagofactura',default=False)


class envio_producto(models.Model):
    _inherit = 'stock.picking'

    @api.depends_context('vendido')
    def pagofact(self):
        self.pago = False
        vendido = self.env['sale.order'].search(
            [('name', '=', self.group_id.name), ('state', '=', 'sale')])
        if vendido.pago == True:
            self.pago = True
            self.state = 'assigned_pagado'
        else:
            self.pago = False

    pago = fields.Boolean(string="¿Pago Generado?", compute='pagofact', default=False)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('assigned_pagado', 'Ready & Paid'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', compute='_compute_state',
        copy=False, index=True, readonly=True, store=True, tracking=True,
        help=" * Draft: The transfer is not confirmed yet. Reservation doesn't apply.\n"
             " * Waiting another operation: This transfer is waiting for another operation before being ready.\n"
             " * Waiting: The transfer is waiting for the availability of some products.\n(a) The shipping policy is \"As soon as possible\": no product could be reserved.\n(b) The shipping policy is \"When all products are ready\": not all the products could be reserved.\n"
             " * Ready: The transfer is ready to be processed.\n(a) The shipping policy is \"As soon as possible\": at least one product has been reserved.\n(b) The shipping policy is \"When all products are ready\": all product have been reserved.\n"
             " * Done: The transfer has been processed.\n"
             " * Cancelled: The transfer has been cancelled.")

class CambioDominioEnRecepcion(models.Model):
    _inherit = 'stock.picking.type'

    count_picking_ready_paid = fields.Integer(compute='_compute_picking_count')
    count_picking_late_paid = fields.Integer(compute='_compute_picking_count')

    def return_actions_to_open_ready_pay(self):
        """ This opens the xml view specified in xml_id for the current vehicle """
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        if xml_id:

            res = self.env['ir.actions.act_window']._for_xml_id('stock.%s' % xml_id)
            res.update(
                context=dict(self.env.context, group_by=False),
                domain=[('scheduled_date', '>', time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),('state', '=', 'assigned_pagado')]
            )
            return res
        return False

    def return_actions_to_open_atrasado(self):
        """ This opens the xml view specified in xml_id for the current vehicle """
        self.ensure_one()
        xml_id = self.env.context.get('xml_id')
        if xml_id:

            res = self.env['ir.actions.act_window']._for_xml_id('stock.%s' % xml_id)
            res.update(
                context=dict(self.env.context, group_by=False),
                domain=[('scheduled_date', '<', time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),('state', '=', 'assigned_pagado'),('picking_type_code', '=', 'outgoing')]
            )
            return res
        return False

    def _compute_picking_count(self):
        # TDE TODO count picking can be done using previous two
        domains = {
            'count_picking_draft': [('state', '=', 'draft')],
            'count_picking_waiting': [('state', 'in', ('confirmed', 'waiting'))],
            'count_picking_ready': [('state', '=', 'assigned')],
            'count_picking_ready_paid': [('scheduled_date', '>', time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),('state', '=', 'assigned_pagado')],
            'count_picking_late_paid': [('scheduled_date', '<', time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)),('state', '=', 'assigned_pagado')],
            'count_picking': [('state', 'in', ('assigned', 'waiting', 'confirmed', 'assigned_pagado'))],
            'count_picking_late': [('scheduled_date', '<', time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)), ('state', 'in', ('assigned', 'waiting', 'confirmed', 'assigned_pagado'))],
            'count_picking_backorders': [('backorder_id', '!=', False), ('state', 'in', ('confirmed', 'assigned', 'waiting', 'assigned_pagado'))],
        }
        for field in domains:
            data = self.env['stock.picking'].read_group(domains[field] +
                [('state', 'not in', ('done', 'cancel')), ('picking_type_id', 'in', self.ids)],
                ['picking_type_id'], ['picking_type_id'])
            count = {
                x['picking_type_id'][0]: x['picking_type_id_count']
                for x in data if x['picking_type_id']
            }
            for record in self:
                record[field] = count.get(record.id, 0)
        for record in self:
            record.rate_picking_late = record.count_picking and record.count_picking_late * 100 / record.count_picking or 0
            record.rate_picking_backorders = record.count_picking and record.count_picking_backorders * 100 / record.count_picking or 0
