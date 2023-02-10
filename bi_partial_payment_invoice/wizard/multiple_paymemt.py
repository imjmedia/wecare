# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccontMultiPaymentWizard(models.Model):
    _name = 'account.multi.payment.wizard'
    _description = 'Account Multiple Payment Wizard'

    @api.model
    def default_get(self, field_vals):
        result = super(AccontMultiPaymentWizard, self).default_get(field_vals)

        if self._context.get('default_partner_type'):
            if self._context.get('default_partner_type') == 'customer':
                result.update({
                    'payment_type' : 'payin'
                })
            else:
                result.update({
                    'payment_type' : 'payout'
                })

        return result

    @api.onchange('move_line_id', 'partner_id')
    def _onchange_payment_id(self):
        for payment in self:
            payment.update({
                'move_lines_ids' : self.env['multi.move.line']
            })

    @api.depends('move_line_id', 'partner_id', 'move_lines_ids')
    def onchange_payment_(self):
        for move in self:
            if not move.move_lines_ids:
                move.last_amount = 0.00
                move.move_line_id.write({
                    'last_amount' : 0.00
                })
            else:
                move.last_amount = move.move_line_id.last_amount


    @api.depends('move_line_id','move_lines_ids',
        'move_lines_ids.amount_to_pay',
        'move_lines_ids.curr_amount_to_pay')
    def compute_payable_amt(self):
        for payment in self:
            amount_residual_currency = amount_residual = 0.0
            remain_amount = remain_amount_currency = 0.0
                
            move_line_id = payment.move_line_id
            transfer_currency_id = payment.currency_id

            if move_line_id:
                amount_residual = abs(move_line_id.amount_residual)
                amount_residual_currency = abs(move_line_id.amount_residual_currency)
            
            if payment.move_lines_ids:
                for line in payment.move_lines_ids:
                    if transfer_currency_id:
                        currency_id = payment.currency_id
                        company_currency_id =  payment.company_currency_id
                        if line.is_comapany:
                            converted_amount = currency_id._convert(\
                                line.curr_amount_to_pay, company_currency_id, payment.company_id, \
                                fields.Date.context_today(self))
                            remain_amount += converted_amount
                            remain_amount_currency += line.curr_amount_to_pay
                    else:
                        remain_amount += line.amount_to_pay
            
            
            if remain_amount > amount_residual:
                raise UserError(_('You can not pay more than Residual Amount'))
            if transfer_currency_id:
                if remain_amount_currency > amount_residual_currency:
                    raise UserError(_('You can not pay more than Residual Amount'))

            remain_amount -= amount_residual
            remain_amount_currency -= amount_residual_currency 

            payment.update({
                'amount_residual' : abs(amount_residual),
                'amount_residual_currency' : abs(amount_residual_currency),
                'remain_amount_currency' : abs(remain_amount_currency),
                'remain_amount' : abs(remain_amount)
            })

    name = fields.Char('Nombre de Pago')
    partner_id = fields.Many2one('res.partner', string='Partner')
    payment_id = fields.Many2one('account.payment', 'Pago Cliente/Proveedor')
    partner_type = fields.Selection([('customer', 'Cliente'), ('supplier', 'Proveedor')], tracking=True)
    payment_type = fields.Selection([('payin', 'Pago de Cliente'), ('payout', 'Pago de Proveedor')], 
        string='Tipo de Pago', required=True, default='payin')
    last_amount = fields.Float('Último Monto', compute='onchange_payment_')
    move_line_id = fields.Many2one('account.move.line', 'Linea de Pago de Cliente/Proveedor')
    company_id = fields.Many2one('res.company', related='move_line_id.company_id', store=True, string='Companía', readonly=False)
    company_currency_id = fields.Many2one('res.currency', string="Divisa de Compañía", related='company_id.currency_id', store=True,
        help='Utility field to express amount currency')
    currency_id = fields.Many2one('res.currency', string="Divisa", related='move_line_id.currency_id', readonly=True, store=True,
        help='Utility field to express amount currency')
    amount_residual = fields.Monetary('Monto Residual', compute="compute_payable_amt", 
        store=True, currency_field="company_currency_id")
    amount_residual_currency = fields.Monetary('Monto Residual de Divisa', 
        compute="compute_payable_amt", 
        store=True, currency_field="currency_id")
    remain_amount = fields.Monetary('Monto Restante', compute="compute_payable_amt",
     store=True, currency_field="company_currency_id")
    remain_amount_currency = fields.Monetary('Monto Restante Divisa', 
        compute="compute_payable_amt", 
        store=True, currency_field="currency_id")
    move_lines_ids = fields.One2many('multi.move.line', 'multi_payment_id',
        string='Pagos Multiples',)


    def multi_partial_pay(self):
        for payment in self:
            if not payment.move_lines_ids:
                return

            link_move_ids = self.env['account.move']

            remaining_payment = 0.00
            move_line = False

            payment_line_id = payment.move_line_id
            payment_move_id = payment.move_line_id.move_id



            current_balance = payment_line_id.debit - payment_line_id.credit

            if payment.currency_id:
                amount_residual = abs(payment_line_id.amount_residual_currency)
            else:
                amount_residual = abs(payment_line_id.amount_residual)

            company_currency = payment.company_currency_id

            currency = payment.currency_id
            company = payment.company_id

            partner_id = payment.partner_id
            payment_id = payment.move_line_id.payment_id

            if payment_id:
                date = payment_id.date or fields.Date.context_today(self)
            else:
                date = fields.Date.context_today(self)

            account_id = payment_line_id.account_id and payment_line_id.account_id.id

            if currency:
                remaining_payment = payment.remain_amount_currency
            else:
                remaining_payment = payment.remain_amount

            remain_payment_move_vals = {}
            line_ids = []

            payment_line_ids = payment_move_id.line_ids.filtered(lambda x: not x.in_payment and x.partner_id == partner_id)

            if payment.partner_type == 'customer':
                payment_line_ids = payment_line_ids.filtered(lambda x : (x.credit > 0 and x.debit == 0) and not x.reconciled)
            else:
                payment_line_ids = payment_line_ids.filtered(lambda x : (x.credit == 0 and x.debit > 0) and not x.reconciled)

            for line in payment_line_ids:
                if line == payment_line_id:
                    line_ids.append(line.id)

            if line_ids:
                line_ids = list(set(line_ids))
                payment_move_id.with_context(check_move_validity=False,skip_account_move_synchronization=True).write({'line_ids' : [(2, line) for line in line_ids]})

            last_line_number = self.env.user.company_id.last_line_number

            for line in payment.move_lines_ids:
                last_line_number += 1
                line_currency_id = line.currency_id

                if currency:
                    if currency == line_currency_id:
                        amount_to_pay = line.curr_amount_to_pay
                    else:
                        amount_to_pay = line_currency_id._convert(\
                        line.amount_to_pay, currency, company, \
                        date)
                else:
                    amount_to_pay = line.amount_to_pay

                if not amount_to_pay:
                    raise UserError(_('No amount for Line %s') % (line.move_id.name))

                if line.currency_id == company_currency:
                    amount_remain = line.amount_to_pay
                else:
                    amount_remain = line.curr_amount_to_pay

                do_payment_move_vals = payment_id.with_context(
                    amount_remain=amount_remain,
                    last_line_number=last_line_number,
                    currency_id = line.currency_id,
                    partner_id=partner_id)._prepare_move_line_default_vals()

                if not payment_id:
                    if currency and currency != company_currency:
                        amount_to_pay = currency._convert(amount_to_pay, company_currency, company, date)
                        amount_currency = amount_to_pay
                        currency_id = currency.id
                    else:
                        amount_to_pay = amount_to_pay
                        amount_currency = 0.0
                        currency_id = False

                    do_payment_move_vals = payment.with_context(
                        amount_to_pay=amount_to_pay,
                        amount_currency=amount_currency,
                        currency_id=currency_id,
                        last_line_number=last_line_number,
                        partner_id=partner_id,
                        current_balance=current_balance,
                        account_id=account_id)._prepare_move_line_default_vals()


                if len(do_payment_move_vals) >= 1:
                    for vals in do_payment_move_vals:
                        vals.update({'move_id':payment_move_id.id})

                        payment_move_id.with_context(check_move_validity=False,skip_account_move_synchronization=True).line_ids.create(vals)

                    if line.move_id.is_inbound():
                        lines = payment_move_id.with_context(check_move_validity=False,skip_account_move_synchronization=True).line_ids.filtered(lambda x : (x.credit > 0 and x.debit == 0) and (x.partner_id == partner_id) and not x.reconciled)
                    else:
                        lines = payment_move_id.with_context(check_move_validity=False,skip_account_move_synchronization=True).line_ids.filtered(lambda x : (x.credit == 0 and x.debit > 0) and (x.partner_id == partner_id) and not x.reconciled)

                    lines += line.move_id.line_ids.filtered(lambda line: line.account_id == lines[0].account_id and not line.reconciled)

                    lines.reconcile()
            

            if remaining_payment:   
                last_line_number += 1
                self.env.user.company_id.write({
                    'last_line_number' : last_line_number
                })

                remain_payment_move_vals = payment_id.with_context(
                    amount_remain=remaining_payment,
                    last_line_number=last_line_number,
                    currency_id = currency or company_currency,
                    partner_id=partner_id)._prepare_move_line_default_vals()

                if not payment_id:
                    if currency and currency != company_currency:
                        amount_remain = currency._convert(remaining_payment, company_currency, company, date)
                        amount_currency = remaining_payment
                        currency_id = currency.id
                    else:
                        amount_remain = remaining_payment
                        amount_currency = 0.0
                        currency_id = False

                    remain_payment_move_vals = payment.with_context(
                        amount_remain=amount_remain,
                        amount_currency=amount_currency,
                        currency_id=currency_id,
                        last_line_number=last_line_number,
                        partner_id=partner_id,
                        current_balance=current_balance,
                        account_id=account_id)._prepare_move_line_default_vals()

                if len(remain_payment_move_vals) >= 1:
                    for vals in remain_payment_move_vals:
                        vals.update({'move_id':payment_move_id.id})    
                    payment_move_id.with_context(check_move_validity=False,skip_account_move_synchronization=True).line_ids.create(vals)
            else:
                self.env.user.company_id.write({
                    'last_line_number' : last_line_number
                })

        return {'type': 'ir.actions.client', 'tag': 'reload'}


    

class MultiMoveLine(models.Model):
    _name = 'multi.move.line'
    _description = 'Account Multiple Payment Wizard'


    multi_payment_id = fields.Many2one('account.multi.payment.wizard', string='Wizard Pago') 
    move_line_id = fields.Many2one('account.move.line', string='Línea de Factura',)
    move_id = fields.Many2one('account.move', string='Factura')
    partner_id = fields.Many2one('res.partner', string='Partner', related="multi_payment_id.partner_id")
    company_id = fields.Many2one('res.company', related='move_id.company_id', store=True, string='Companía', readonly=False)
    company_currency_id = fields.Many2one('res.currency', string="Divisa de Compañía", related='company_id.currency_id', 
        help='Utility field to express amount currency')
    currency_id = fields.Many2one('res.currency', string="Divisa", related='move_id.currency_id', readonly=True,
        help='Utility field to express amount currency')
    payment_type = fields.Selection(related='multi_payment_id.payment_type', string="Tipo de Pago", store=True, readonly=True)
    amount_total = fields.Monetary(string='Monto Total', store=True, 
        related="move_id.amount_total", default=0.00)
    amount_residual = fields.Monetary(string='Monto Residual', readonly=True,
        default=0.00, currency_field='company_currency_id')
    amount_residual_currency = fields.Monetary(string='Monto Residual de Divisa', readonly=True,
        default=0.00, currency_field='currency_id')
    is_comapany = fields.Boolean('Es Companía?')
    amount_to_pay = fields.Monetary(string='Monto a Pagar', default=0.00, currency_field='company_currency_id')
    payment_curr_id = fields.Many2one('res.currency', string="Divisa de Pago", 
        related='multi_payment_id.currency_id')
    curr_amount_to_pay = fields.Monetary(string='Monto de Divisa a Pagar', default=0.00, currency_field='payment_curr_id')


    @api.onchange('move_id')
    def compute_order_amount(self):
        for sale in self:
            payment_curr_id = sale.multi_payment_id.currency_id

            amount_residual = amount_residual_currency = 0.0
            if sale.move_id:
                for line in sale.move_id.line_ids:
                    amount_residual += line.amount_residual
                    amount_residual_currency += line.amount_residual_currency

            sale.amount_residual = amount_residual
            sale.amount_residual_currency = amount_residual_currency

            if payment_curr_id:
                sale.is_comapany = True
            else:
                sale.is_comapany = False


    @api.onchange('amount_to_pay')
    def onchange_amount_to_pay(self):
        for sale in self:
            payment_curr_id = sale.multi_payment_id.currency_id
            if not sale.is_comapany:
                payment_curr_id = sale.currency_id
                company_currency_id = sale.company_id.currency_id
                company_id = sale.company_id
                if sale.currency_id != sale.company_id.currency_id:
                    sale.curr_amount_to_pay = company_currency_id._convert(
                        sale.amount_to_pay, 
                        payment_curr_id,
                        company_id, 
                        fields.Date.context_today(self))

    @api.onchange('curr_amount_to_pay')
    def onchange_curr_amount_to_pay(self):
        for sale in self:
            payment_curr_id = sale.multi_payment_id.currency_id
            company_currency_id = sale.company_id.currency_id
            company_id = sale.company_id
            if sale.is_comapany:
                if company_id and company_currency_id:
                    converted_amount = payment_curr_id._convert(
                        sale.curr_amount_to_pay, 
                        company_currency_id, 
                        company_id, 
                        fields.Date.context_today(self))
                    sale.amount_to_pay = converted_amount