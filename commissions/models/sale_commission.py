# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)

class PricelistConmission(models.Model):
    _inherit = ['product.pricelist']

    type_id = fields.Many2one('product.pricelist_type', string="Tipos de Lista", track_visibility='onchange')
                            

class PricelistPrice(models.Model):
    _description = "Pricelist types"    
    _name = 'product.pricelist_type'
    
    name = fields.Char(string="Nombre", required=True)
    description = fields.Text(string="Descripción")
    comision = fields.Float(string="% de Comision")


class SaleCommission(models.Model):
    _description = "Sale Commission"
    _name = 'sale.commission'
    _inherit = ['mail.activity.mixin', 'mail.thread']
    _order = 'id desc'

    def _get_company_currency(self):
        self.currency_id = self.env.user.company_id.currency_id

    name = fields.Char('Code', translate=True, default="New", copy=False)
    entry_date = fields.Datetime('Date', default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', string='Responsible', track_visibility='onchange', default=lambda self: self.env.user)
    commercial_id = fields.Many2one('res.users', string='Commercial', track_visibility='onchange')
    date_from = fields.Date(string='Date From', default=fields.Date.context_today, track_visibility='onchange')
    date_to = fields.Date(string='Date To', default=fields.Date.context_today, track_visibility='onchange')
    commission_lines = fields.One2many('sale.commission.line', 'parent_id', string='Lines')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Open'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled')],
        string='State', index=True, readonly=True, default='draft', copy=False)
    currency_id = fields.Many2one('res.currency', compute='_get_company_currency', readonly=True, string="Currency", help='Utility field to express amount currency')
    amount_total = fields.Float('Commission total')
    benefit_total = fields.Float('Total benefit')
    margin_total = fields.Float('Total margin (%)')
    sale_total = fields.Float('Total')

    @api.model
    def create(self, vals):
        if vals.get('name', "New") == "New":
            vals['name'] = self.env['ir.sequence'].next_by_code('sale.commission') or "New"
        return super(SaleCommission, self).create(vals)

    def unlink(self):
        for record in self:
            if record.state in ['paid']:
                raise UserError(_('You cannot delete a commission in "Paid" status. Contact an Administrator or Manager.'))
            else:
                sale_commission_id = self.env['sale.commission.line'].search([('parent_id', '=', record.id)])
                if sale_commission_id:
                    for sale_commission in sale_commission_id:
                        sale_commission.unlink()
        return super(SaleCommission, self).unlink()

    def action_confirm(self):
        self.state = 'done'

    def action_paid(self):
        self.state = 'paid'

    def action_cancel(self):
        self.state = 'cancel'

    def action_draft(self):
        self.state = 'draft'

    def action_commission(self):
        cont_line = 0
        val_margin = 0
        for obj_commision in self:
            if obj_commision.date_to and obj_commision.date_from:
                payments_ids = self.env['account.payment'].search([('state', '=', 'posted'), ('payment_type', '=', 'inbound')])
                pagos_filtered = payments_ids.filtered(lambda e: obj_commision.date_from <= e.date <= obj_commision.date_to)
                commission_type = self.env['ir.config_parameter'].sudo().get_param('commission_type')
                obj_commision.commission_lines.unlink()
                for pago in pagos_filtered:
                    for factura in pago.reconciled_invoice_ids:
                        sales_ids = factura.invoice_line_ids.mapped('sale_line_ids.order_id')
                        if sales_ids:
                            for order in sales_ids.filtered(lambda e: e.user_id.id == obj_commision.commercial_id.id):
                                if not order.dont_calculate:
                                    if commission_type == 'net':
                                        commision_val = order.net_margin
                                    else:
                                        commision_val = order.gross_margin
                                    commission_calc = order.pricelist_id.type_id.comision
                                    amount = commision_val * float(commission_calc) / 100
                                    if amount:
                                        vals = {
                                            'user_id': obj_commision.commercial_id.id,
                                            'amount': amount,
                                            'parent_id': obj_commision.id,
                                            'benefit_net': commision_val,
                                            'margin_net': order.net_margin_por,
                                            'invoice_id': factura.id,
                                            'payment_id': pago.id,
                                            'order_id': order.id,
                                            'partner_id': order.partner_id.id,
                                            'sale_amount': order.amount_untaxed

                                        }
                                        comi_obj = self.env['sale.commission.line'].search([('invoice_id', '=', factura.id)])
                                        if not comi_obj:
                                            self.env['sale.commission.line'].create(vals)
                                            cont_line += 1
                                        val_margin += order.net_margin_por
                                        obj_commision.benefit_total += commision_val
                                        if cont_line > 0:
                                            obj_commision.margin_total = val_margin / cont_line
                                            obj_commision.amount_total += amount
                                            obj_commision.sale_total += order.amount_untaxed



        """
        for obj_commision in self: #método original
            val_margin = 0
            cont_line = 0
            obj_commision.benefit_total = 0
            obj_commision.margin_total = 0
            obj_commision.amount_total = 0
            obj_commision.sale_total = 0
            commission_type = self.env['ir.config_parameter'].sudo().get_param('commission_type')
            commission_calc = self.env['ir.config_parameter'].sudo().get_param('commission_value')
            if commission_type and commission_calc and obj_commision.commercial_id and obj_commision.date_to and obj_commision.date_from:
                invoices_ids = self.env['account.move'].search([('state', 'not in', ['draft', 'cancel']), ('move_type', 'in', ['out_invoice', 'out_refund'])])
                invoices_filtered = invoices_ids.filtered(lambda e: obj_commision.date_from <= e.invoice_date <= obj_commision.date_to)
                self.env['sale.commission.line'].search([('parent_id', '=', obj_commision.id)]).unlink()
                if invoices_filtered:
                    for invoice in invoices_filtered:
                        factor = 0
                        if invoice.move_type == 'out_invoice':
                            origin = invoice.invoice_origin
                            factor = 1
                        if invoice.move_type == 'out_refund':
                            invoices_id = self.env['account.move'].search([('number', '=', invoice.invoice_origin)], limit=1)
                            if invoices_id:
                                origin = invoice.invoice_origin
                                factor = -1
                        if factor != 0:
                            if origin:
                                _logger.info('Invoice %s, origin %s' % (invoice.name, origin))
                                sales_ids = self.env['sale.order'].search(['|', ('name', '=', origin), ('origin', 'like', origin)])
                                if sales_ids:
                                    for order in sales_ids.filtered(lambda e: e.user_id.id == obj_commision.commercial_id.id):
                                        if not order.dont_calculate:
                                            if commission_type == 'net':
                                                commision_val = order.net_margin
                                            else:
                                                commision_val = order.gross_margin
                                            if order.user_id.commission_user_rate > 0:
                                                commission_calc = order.user_id.commission_user_rate
                                            amount = commision_val * float(commission_calc) / 100 * factor
                                            if amount:
                                                vals = {
                                                    'user_id': obj_commision.commercial_id.id,
                                                    'amount': amount,
                                                    'parent_id': obj_commision.id,
                                                    'benefit_net': commision_val,
                                                    'margin_net': order.net_margin_por,
                                                    'invoice_id': invoice.id,
                                                    #'user_id': order.user_id.id,
                                                    'order_id': order.id,
                                                    'partner_id': order.partner_id.id,
                                                    'sale_amount': order.amount_untaxed
                                                }
                                                comi_obj = self.env['sale.commission.line'].search([('invoice_id', '=', invoice.id)])
                                                if not comi_obj:
                                                    self.env['sale.commission.line'].create(vals)
                                                    cont_line += 1
                                                val_margin += order.net_margin_por
                                                obj_commision.benefit_total += commision_val
                                                if cont_line > 0:
                                                    obj_commision.margin_total = val_margin / cont_line
                                                    obj_commision.amount_total += amount
                                                    obj_commision.sale_total += order.amount_untaxed """


class SaleCommissionLine(models.Model):
    _name = 'sale.commission.line'
    _description = 'Sale Commission Line'
    _rec_name = "parent_id"

    def _get_company_currency(self):
        self.currency_id = self.env.user.company_id.currency_id

    parent_id = fields.Many2one('sale.commission')
    user_id = fields.Many2one('res.users')
    amount = fields.Float('Commission')
    benefit_net = fields.Float('Benefit')
    margin_net = fields.Float('Margin (%)')
    sale_amount = fields.Float('Amount')
    invoice_id = fields.Many2one('account.move')
    partner_id = fields.Many2one('res.partner', string='Client', track_visibility='onchange')
    order_id = fields.Many2one('sale.order', string='SO', track_visibility='onchange')
    currency_id = fields.Many2one('res.currency', compute='_get_company_currency', readonly=True, string="Currency", help='Utility field to express amount currency')
    payment_id=fields.Many2one('account.payment')
    pago_amount = fields.Float('Monto de pago')

