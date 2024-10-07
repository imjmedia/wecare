# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)

class ProductPricelist(models.Model):
    _inherit = ['product.pricelist']

    type_id = fields.Many2one('product.pricelist_type', string="Tipos de Lista", tracking=True)
                            

class ProductPricelistType(models.Model):
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
    user_id = fields.Many2one('res.users', string='Responsible', tracking=True, default=lambda self: self.env.user)
    commercial_id = fields.Many2one('res.users', string='Commercial', tracking=True)
    date_from = fields.Date(string='Date From', default=fields.Date.context_today, tracking=True)
    date_to = fields.Date(string='Date To', default=fields.Date.context_today, tracking=True)
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
    commission_resume = fields.One2many('sale.commission.resume', 'parent_id', string='Resumen Lines')

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
        resumen_montos={}   
        for obj_commision in self:
            obj_commision.margin_total = 0
            obj_commision.amount_total = 0
            obj_commision.sale_total = 0    
            if obj_commision.date_to and obj_commision.date_from:
                payments_ids = self.env['account.payment'].search([('state', '=', 'posted'), ('payment_type', '=', 'inbound')])
                pagos_filtered = payments_ids.filtered(lambda e: obj_commision.date_from <= e.date <= obj_commision.date_to)
                #_logger.info(pagos_filtered)
                #_logger.info('Pago %s, origin %s' % (invoice.name, origin))
                commission_type = self.env['ir.config_parameter'].sudo().get_param('commission_type')
                obj_commision.commission_lines.unlink()
                
                #Primer ciclo para determinar el monto de los pagos de corporativo.
                resumen_corpo={}
                for pago in pagos_filtered:
                    if pago.partner_id.partner_corp_id:
                        partner_id = pago.partner_id.partner_corp_id.id
                        if partner_id in resumen_corpo:
                            resumen_corpo[partner_id]['total'] += pago.amount
                        else:
                            resumen_corpo[partner_id] = {'total': pago.amount}
                #_logger.info('Resumen Montos %s' %(resumen_corpo))
                com_corp = {}  #diccionario que guardara el id corporativo y su comisión segun la tabla
                for partner_id, valores in resumen_corpo.items():
                    partner = self.env['res.partner'].browse(partner_id)
                    total = valores['total']
                    valores['partner_id'] = partner.id
                    com = 0
                    if total > 1000000:
                        com = 1
                    elif total > 500000:
                        com = 1.5
                    elif total > 0:
                        com = 2
                    valores['com'] = com
                    valores[partner_id] = com
                    com_corp[partner_id] = com
                    #_logger.info('Partner: %s, Total: %s, Com: %s' % (partner.name, total, com))
                    #_logger.info('Valores: %s' % (valores))
                    #_logger.info('com_corp: %s' % (com_corp))

                
                for pago in pagos_filtered:
                    #_logger.info('-------Pago %s, Id Pago %s' %(pago.display_name, pago.id))
                    #_logger.info(pago.reconciled_invoice_ids)
                    cliente_id = pago.partner_id.id
                    corp_id= pago.partner_id.partner_corp_id.id
                    #amount_paid= pago.amount
                    #_logger.info(pago.reconciled_invoice_ids)
                    for factura in pago.reconciled_invoice_ids:
                        #sales_ids = factura.invoice_line_ids.mapped('sale_line_ids.order_id')
                        #_logger.info('Factura %s' % (factura.name))
                        #_logger.info(factura._get_reconciled_payments())
                        parciales = factura._compute_payments_widget_reconciled_info()
                        _logger.info('Parciales %s' % (parciales))
                        if parciales:
                            for pagos in parciales:  #Obtener solo el pago de la factura 
                                #_logger.info(pagos.get('name'))
                                #_logger.info(pagos.get('account_payment_id'))
                                if pago.id==pagos.get('account_payment_id'):
                                    #_logger.info(pagos.get('amount'))
                                    amount_paid=pagos.get('amount')
                        #_logger.info(factura._get_reconciled_statement_lines())
                        #_logger.info(factura._get_reconciled_invoices())
                        #_logger.info(factura._get_reconciled_invoices_partials())
                        if factura.invoice_origin:
                            sales_ids = self.env['sale.order'].search(['|', ('name', '=', factura.invoice_origin), ('origin', 'like', factura.invoice_origin)])
                        #_logger.info(sales_ids)
                        if sales_ids:
                            for order in sales_ids.filtered(lambda e: e.user_id.id == obj_commision.commercial_id.id):
                                if commission_type == 'net':
                                    commision_val = order.net_margin
                                else:
                                    commision_val = order.gross_margin
                                if corp_id: # En caso de ser corporativo toma la comisión corporativa
                                    partner_corp = self.env['res.partner'].browse(corp_id)
                                    #_logger.info('Comision Corpo: %s' % (com_corp[(partner_corp.id)]))
                                    commission_calc = com_corp[(partner_corp.id)]                              
                                    montonoiva = round(amount_paid/1.16,2)
                                    amount =  round(montonoiva * float(commission_calc) / 100,2)
                                else:
                                    commission_calc = order.pricelist_id.type_id.comision                                
                                    montonoiva = round(amount_paid/1.16,2)
                                    amount =  round(montonoiva * float(commission_calc) / 100,2)
                                
                                #_logger.info('Monto Pagado %s, MontoSinIVA %s, Comm %s,MontoCom %s' %(amount_paid,montonoiva,commission_calc,amount))
                                #_logger.info('Comision %s' %(order.pricelist_id.type_id.comision))
                                #_logger.info('Pago_id %s' %(pago.id))
                                if amount:
                                    vals = {
                                        'user_id': obj_commision.commercial_id.id,
                                        'amount': amount,
                                        'parent_id': obj_commision.id,
                                        'benefit_net': commision_val,
                                        'margin_net': commission_calc,
                                        'invoice_id': factura.id,
                                        'payment_id': pago.id,
                                        'payment_date': pago.date, 
                                        'order_id': order.id,
                                        'partner_id': order.partner_id.id,
                                        'partner_corp_id':order.partner_id.partner_corp_id.id,
                                        'sale_amount': montonoiva

                                    }
                                    # comi_obj = self.env['sale.commission.line'].search([('invoice_id', '=', factura.id)])
                                    # if not comi_obj:
                                    self.env['sale.commission.line'].create(vals)
                                    cont_line += 1
                                    val_margin += order.net_margin_por
                                    obj_commision.benefit_total += commision_val
                                    if cont_line > 0:
                                        obj_commision.margin_total = val_margin / cont_line
                                        obj_commision.amount_total += montonoiva
                                        obj_commision.sale_total += amount

                    if cliente_id in resumen_montos:
                        resumen_montos[cliente_id] += pago.amount
                    else:
                        resumen_montos[cliente_id] = pago.amount
                        #_logger.info(resumen_montos)


        # Sumatoria agrupada por partner_id

        obj_commision.commission_resume.unlink()
        partner_totals = {}

        for com_line in self.env['sale.commission.line'].search([('parent_id', '=', obj_commision.id)]):
            if com_line.partner_id.partner_corp_id.id:
                partner_id = com_line.partner_id.partner_corp_id.id
            else:
                partner_id = com_line.partner_id.id
            amount = com_line.amount
            
            if partner_id in partner_totals:
                partner_totals[partner_id] += round(amount,2)
            else:
                partner_totals[partner_id] = round(amount,2)
            if partner_totals[partner_id] > 30000:
                partner_totals[partner_id]=30000
        
        _logger.info(partner_totals)
        _logger.info('Sumatoria agrupada por partner_id:')
        
        for partner_id, total in partner_totals.items():
            partner = self.env['res.partner'].browse(partner_id)
            _logger.info('Partner: %s, Total: %s' % (partner.name, total)) 
            
        # Crear registros en SaleCommissionResume
        resume_records = self.env['sale.commission.resume'].create_resume_records(partner_totals, obj_commision)
    
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
    partner_id = fields.Many2one('res.partner', string='Client', tracking=True)
    partner_corp_id = fields.Many2one('res.partner', string='Corporation', tracking=True)
    order_id = fields.Many2one('sale.order', string='SO', tracking=True)
    currency_id = fields.Many2one('res.currency', compute='_get_company_currency', readonly=True, string="Currency", help='Utility field to express amount currency')
    payment_id=fields.Many2one('account.payment')
    payment_date = fields.Date(string='Payment Date')
    pago_amount = fields.Float('Monto de pago')


    
class SaleCommissionResume(models.Model):
    _name = 'sale.commission.resume'
    _description = 'Sale Commission Lines Resume'
    _rec_name = "parent_id"

    def _get_company_currency(self):
        self.currency_id = self.env.user.company_id.currency_id

    parent_id = fields.Many2one('sale.commission')
    user_id = fields.Many2one('res.users')
    amount = fields.Float('Commission')
    amount_max =fields.Float('Amount Max')
    partner_id = fields.Many2one('res.partner', string='Client')
    currency_id = fields.Many2one('res.currency', compute='_get_company_currency', readonly=True, string="Currency", help='Utility field to express amount currency')
    #payment_id=fields.Many2one('account.payment')
    #pago_amount = fields.Float('Monto de pago')

    def create_resume_records(self, partner_totals, obj_commision):
        resume_records = []
        for partner_id, total in partner_totals.items():
            partner = self.env['res.partner'].browse(partner_id)
            resume_record = self.create({
                'parent_id':  obj_commision.id,
                'user_id': obj_commision.commercial_id.user_id.id,
                'amount': total,
                'partner_id': partner.id,
                'amount_max':30000,
            })
            resume_records.append(resume_record)
        return resume_records

