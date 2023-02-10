# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccontPaymentWizard(models.Model):
    _name = 'account.payment.wizard'
    _description = 'Account Payment Wizard'

    @api.model
    def default_get(self, field_vals):
        result = super(AccontPaymentWizard, self).default_get(field_vals)

        if self._context.get('payment_value'):
            payment_value = self._context.get('payment_value')

            move_id = payment_value['move_id']

            line_values = payment_value['content']

            current_line = self._context.get('line_id')

            amount = 0.00
            name = '/'

            for line in line_values:
                move_line_id = line.get('id')
                if int(current_line) == int(move_line_id):
                    amount = line.get('amount')
                    name = line.get('journal_name')
                    
                    result.update({
                        'move_id' : int(move_id),
                        'move_line_id' : int(move_line_id),
                        'amount_total' : amount or 0.00,
                        'name' : name
                    })
                    return result
        return result

    @api.depends('amount_total', 'amount_to_pay', 'amount_residual')
    def remain_amount_(self):
        for payment in self:
            amount = payment.amount_total - payment.amount_to_pay
            due_amount = payment.amount_residual - payment.amount_to_pay
            payment.amount_remain = amount or 0.00
            payment.amount_due_remain = due_amount or 0.00


    name = fields.Char('Nombre de Pago')
    move_id = fields.Many2one('account.move','Factura')
    company_id = fields.Many2one('res.company', related='move_id.company_id', store=True, string='Companía', readonly=False)
    company_currency_id = fields.Many2one('res.currency', string="Divisa de Companía", related='company_id.currency_id', readonly=True,
        help='Utility field to express amount currency')
    amount_to_pay = fields.Monetary(string='Monto a Pagar', default=0.00)
    amount_remain = fields.Monetary(string='Monto Restante de Pago', store=True, readonly=True, 
        compute='remain_amount_')
    amount_due_remain = fields.Monetary(string='Monto Restante de Factura', store=True, readonly=True, 
        compute='remain_amount_')
    amount_total = fields.Monetary('Monto Total', default=0.00)
    move_line_id = fields.Many2one('account.move.line','Línea de Factura')
    payment_id = fields.Many2one('account.payment', related='move_line_id.payment_id', store=True, string='Pago')
    amount_residual = fields.Monetary(string='Monto Adeudado', store=True, readonly=True,
        related="move_id.amount_residual")
    currency_id = fields.Many2one('res.currency', string="Divisa", related='move_id.currency_id', readonly=True,
        help='Utility field to express amount currency')
    amount_currency = fields.Monetary('Monto en Divisa')

    def partial_pay(self):
        for payment in self:
            payment_move_id = payment.move_line_id.move_id

            partner_id = payment.move_line_id.partner_id

            remain_payment_move_vals = {}

            if payment.amount_to_pay > payment.amount_residual:
                raise UserError(_('No puedes pagar más del monto restante. !!!'))

            if payment.amount_remain < 0.00:
                raise UserError(_('No puedes pagar más del monto restante. !!!'))

            if payment.payment_id:
                date = payment.payment_id.date or fields.Date.context_today(self)
            else:
                date = payment_move_id.invoice_date or fields.Date.context_today(self)

            last_line_number = self.env.user.company_id.last_line_number

            last_line_number += 1

            if payment.payment_id.currency_id != payment.currency_id:
                amount_to_pay = payment.currency_id._convert(payment.amount_to_pay, payment.payment_id.currency_id, payment.company_id, date)
            else:   
                amount_to_pay = payment.amount_to_pay

            do_payment_move_vals = payment.payment_id.with_context(
                amount_to_pay=payment.amount_to_pay,
                last_line_number=last_line_number,
                currency_id = payment.currency_id,
                partner_id=partner_id)._prepare_move_line_default_vals()

            if not payment.payment_id:
                if payment.currency_id != payment.company_currency_id:
                    amount_to_pay = payment.currency_id._convert(payment.amount_to_pay, payment.company_currency_id, payment.company_id, date)
                    amount_currency = payment.amount_to_pay
                    currency_id = payment.currency_id.id
                else:
                    amount_to_pay = payment.amount_to_pay
                    amount_currency = 0.0
                    currency_id = False

                do_payment_move_vals = payment.with_context(
                    amount_to_pay=amount_to_pay,
                    amount_currency=amount_currency,
                    currency_id=currency_id,
                    last_line_number=last_line_number,
                    partner_id=partner_id)._prepare_move_line_default_vals()

                

            do_last_number = last_line_number


            if payment.amount_remain:
                last_line_number += 1
                self.env.user.company_id.write({
                    'last_line_number' : last_line_number
                })

                if payment.currency_id:
                    amount_remain = payment.currency_id._convert(payment.amount_remain, payment.company_currency_id, payment.company_id, date)
                else:
                    amount_remain = payment.amount_remain

                remain_payment_move_vals = payment.payment_id.with_context(
                    amount_remain=payment.amount_remain,
                    last_line_number=last_line_number,
                    currency_id = payment.currency_id,
                    partner_id=partner_id)._prepare_move_line_default_vals()


              

                if not payment.payment_id:
                    if payment.currency_id != payment.company_currency_id:
                        amount_remain = payment.currency_id._convert(payment.amount_remain, payment.company_currency_id, payment.company_id, date)
                        amount_currency = payment.amount_remain
                        currency_id = payment.currency_id.id
                    else:
                        amount_remain = payment.amount_remain
                        amount_currency = 0.0
                        currency_id = False

                    remain_payment_move_vals = payment.with_context(
                        amount_remain=amount_remain,
                        amount_currency=amount_currency,
                        currency_id=currency_id,
                        last_line_number=last_line_number,
                        partner_id=partner_id)._prepare_move_line_default_vals()


            else:
                self.env.user.company_id.write({
                    'last_line_number' : last_line_number
                })

            line_ids = []


            payment_line_ids = payment_move_id.line_ids.filtered(lambda x: not x.in_payment and (x.partner_id == partner_id))
            if payment.move_id.is_inbound():
                payment_line_ids = payment_line_ids.filtered(lambda x : (x.credit > 0 and x.debit == 0) and not x.reconciled)
            else:
                payment_line_ids = payment_line_ids.filtered(lambda x : (x.credit == 0 and x.debit > 0) and not x.reconciled)

            for line in payment_line_ids:
                if line == payment.move_line_id:
                    line_ids.append(line.id)
            if line_ids:
                payment_move_id.with_context(check_move_validity=False,skip_account_move_synchronization=True).write({'line_ids' : [(2, line) for line in line_ids]})
            if do_payment_move_vals:
                for vals in do_payment_move_vals:
                    vals.update({'move_id':payment_move_id.id})
                    payment_move_id.with_context(check_move_validity=False,skip_account_move_synchronization=True).line_ids.create(vals)

                if payment.move_id.is_inbound():
                    lines = payment_move_id.with_context(check_move_validity=False,skip_account_move_synchronization=True).line_ids.filtered(lambda x : (x.credit > 0 and x.debit == 0)  and (x.partner_id == partner_id) and not x.reconciled and x.last_line_number == do_last_number)
                
                else:
                    lines = payment_move_id.with_context(check_move_validity=False,skip_account_move_synchronization=True).line_ids.filtered(lambda x : (x.credit == 0 and x.debit > 0)  and (x.partner_id == partner_id) and not x.reconciled and x.last_line_number == do_last_number)

                if lines:
                    lines += payment.move_id.line_ids.filtered(lambda line: line.account_id == lines[0].account_id and not line.reconciled)
                    if payment.amount_remain:
                        if len(remain_payment_move_vals) >= 1:
                            for vals in remain_payment_move_vals:
                                vals.update({'move_id':payment_move_id.id})
                                payment_move_id.with_context(check_move_validity=False,skip_account_move_synchronization=True).line_ids.create(vals)

                    lines.with_context(orignal_amount=payment.amount_to_pay).reconcile()
                else:
                    raise UserError(_('Algo ha salido mal. Intenta otra vez.'))
        return {'type': 'ir.actions.client', 'tag': 'reload'}

 

