# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import re
from odoo.osv import expression
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from datetime import date, timedelta
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re

class ResCompany(models.Model):
    _inherit = 'res.company'

    last_move_number = fields.Integer('Last Move Number', default=1)
    last_line_number = fields.Integer('Last Line Number', default=0)


class ResUsers(models.Model):
    _inherit = 'res.users'

    account_id = fields.Many2one('account.account', 'Bank Account')    


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    manual_partner_id = fields.Many2one('res.partner', string='Manual Partner')


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    ref_text = fields.Text(string='Voucher Reference')
    report_user_id = fields.Many2one('res.users', string='Responsible', 
        required=False, compute="compute_user_date")
    report_date = fields.Date(required=False, string="Date",
        index=True, copy=False, compute="compute_user_date")

    def compute_user_date(self):
        for record in self:
            today = datetime.today()
            user = self.env.user.id
            record.update({
                'report_date' : today,
                'report_user_id' : user
            })

    @api.constrains('line_ids', 'journal_id')
    def _validate_move_modification(self):
        if 'posted' in self.mapped('line_ids.payment_id.state'):
            pass


    def button_draft(self):
        AccountMoveLine = self.env['account.move.line']
        excluded_move_ids = []

        if self._context.get('suspense_moves_mode'):
            excluded_move_ids = AccountMoveLine.search(AccountMoveLine._get_suspense_moves_domain() + [('move_id', 'in', self.ids)]).mapped('move_id').ids

        for move in self:
            if move in move.line_ids.mapped('full_reconcile_id.exchange_move_id'):
                raise UserError(_('You cannot reset to draft an exchange difference journal entry.'))
            if move.tax_cash_basis_rec_id:
                raise UserError(_('You cannot reset to draft a tax cash basis journal entry.'))
            if move.restrict_mode_hash_table and move.state == 'posted' and move.id not in excluded_move_ids:
                raise UserError(_('You cannot modify a posted entry of this journal because it is in strict mode.'))
            # We remove all the analytics entries for this journal
            move.mapped('line_ids.analytic_line_ids').unlink()

        if not self._context.get('no_remove'):
            self.mapped('line_ids').remove_move_reconcile()
        self.write({'state': 'draft'})


    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []

        state = ['posted']
        payment_state = ['not_paid', 'in_payment','partial']


        if self._context.get('partner_id') and self._context.get('type'):
            partner_id = int(self._context.get('partner_id'))

            currency_id = self._context.get('currency_id')

            if not currency_id:
                currency_id = self.env.company.currency_id.id
            
            if self._context.get('type') == 'payin':
                move_type = 'out_invoice'
            else:
                move_type = 'in_invoice'
            
            args += [('partner_id','=',partner_id),('move_type','=',move_type),
            ('state','in',state),('payment_state','in',payment_state)]

        return super(AccountMoveInherit, self)._name_search(name=name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid)

class AccountMoveLineInherit(models.Model):
    _inherit = 'account.move.line'

    @api.depends('matched_debit_ids','matched_credit_ids')
    def compute_partial_matching_number(self):
        for line in self:
            partial_matching_number = []
            if line.matched_credit_ids:
                for credit in line.matched_credit_ids:
                    partial_matching_number.append('PM' + str(credit.id))
            if line.matched_debit_ids:
                for debit in line.matched_debit_ids:
                    partial_matching_number.append('PM' + str(debit.id))
            line.partial_matching_number = ', '.join(partial_matching_number)


    partial_matching_number = fields.Char(string='Partial matching', compute='compute_partial_matching_number', store=True)
    in_payment = fields.Boolean('In Payment')
    last_line_number = fields.Integer('Last Line Number', default=0)
    last_amount = fields.Float('Last Amount', default=0.00)
    
    def unlink(self):
        
        moves = self.mapped('move_id')
        for move in moves:
            move.update({'state':'draft'})
        return super(AccountMoveLineInherit,self).unlink()

    def check_full_reconcile(self):
        """
        This method check if a move is totally reconciled and if we need to create exchange rate entries for the move.
        In case exchange rate entries needs to be created, one will be created per currency present.
        In case of full reconciliation, all moves belonging to the reconciliation will belong to the same account_full_reconcile object.
        """
        # Get first all aml involved
        todo = self.env['account.partial.reconcile'].search_read(['|', ('debit_move_id', 'in', self.ids), ('credit_move_id', 'in', self.ids)], ['debit_move_id', 'credit_move_id'])
        amls = set(self.ids)
        seen = set()
        while todo:
            aml_ids = [rec['debit_move_id'][0] for rec in todo if rec['debit_move_id']] + [rec['credit_move_id'][0] for rec in todo if rec['credit_move_id']]
            amls |= set(aml_ids)
            seen |= set([rec['id'] for rec in todo])
            todo = self.env['account.partial.reconcile'].search_read(['&', '|', ('credit_move_id', 'in', aml_ids), ('debit_move_id', 'in', aml_ids), '!', ('id', 'in', list(seen))], ['debit_move_id', 'credit_move_id'])

        partial_rec_ids = list(seen)
        if not amls:
            return
        else:
            amls = self.browse(list(amls))

        # If we have multiple currency, we can only base ourselves on debit-credit to see if it is fully reconciled
        currency = set([a.currency_id for a in amls if a.currency_id.id != False])
        multiple_currency = False
        if len(currency) != 1:
            currency = False
            multiple_currency = True
        else:
            currency = list(currency)[0]
        # Get the sum(debit, credit, amount_currency) of all amls involved
        total_debit = 0
        total_credit = 0
        total_amount_currency = 0
        maxdate = date.min
        to_balance = {}
        cash_basis_partial = self.env['account.partial.reconcile']
        for aml in amls:
            cash_basis_partial |= aml.move_id.tax_cash_basis_rec_id
            total_debit += aml.debit
            total_credit += aml.credit
            maxdate = max(aml.date, maxdate)
            total_amount_currency += aml.amount_currency
            # Convert in currency if we only have one currency and no amount_currency
            if not aml.amount_currency and currency:
                multiple_currency = True
                total_amount_currency += aml.company_id.currency_id._convert(aml.balance, currency, aml.company_id, aml.date)
            # If we still have residual value, it means that this move might need to be balanced using an exchange rate entry
            if aml.amount_residual != 0 or aml.amount_residual_currency != 0:
                if not to_balance.get(aml.currency_id):
                    to_balance[aml.currency_id] = [self.env['account.move.line'], 0]
                to_balance[aml.currency_id][0] += aml
                to_balance[aml.currency_id][1] += aml.amount_residual != 0 and aml.amount_residual or aml.amount_residual_currency

        # Check if reconciliation is total
        # To check if reconciliation is total we have 3 different use case:
        # 1) There are multiple currency different than company currency, in that case we check using debit-credit
        # 2) We only have one currency which is different than company currency, in that case we check using amount_currency
        # 3) We have only one currency and some entries that don't have a secundary currency, in that case we check debit-credit
        #   or amount_currency.
        # 4) Cash basis full reconciliation
        #     - either none of the moves are cash basis reconciled, and we proceed
        #     - or some moves are cash basis reconciled and we make sure they are all fully reconciled

        digits_rounding_precision = amls[0].company_id.currency_id.rounding
        if (
                (
                    not cash_basis_partial or (cash_basis_partial and all([p >= 1.0 for p in amls._get_matched_percentage().values()]))
                ) and
                (
                    currency and float_is_zero(total_amount_currency, precision_rounding=currency.rounding) or
                    multiple_currency and float_compare(total_debit, total_credit, precision_rounding=digits_rounding_precision) == 0
                )
        ):

            exchange_move_id = False
            missing_exchange_difference = False
            # Eventually create a journal entry to book the difference due to foreign currency's exchange rate that fluctuates
            if to_balance and any([not float_is_zero(residual, precision_rounding=digits_rounding_precision) for aml, residual in to_balance.values()]):
                if not self.env.context.get('no_exchange_difference'):
                    exchange_move_vals = self.env['account.full.reconcile']._prepare_exchange_diff_move(
                        move_date=maxdate, company=amls[0].company_id)
                    if len(amls.mapped('partner_id')) == 1 and amls[0].partner_id:
                        exchange_move_vals['partner_id'] = amls[0].partner_id.id
                    
                    exchange_move = self.env['account.move'].with_context(default_type='entry').create(exchange_move_vals)
                    part_reconcile = self.env['account.partial.reconcile']
                    for aml_to_balance, total in to_balance.values():
                        if total:
                            rate_diff_amls, rate_diff_partial_rec = part_reconcile.create_exchange_rate_entry(aml_to_balance, exchange_move)
                            amls += rate_diff_amls
                            partial_rec_ids += rate_diff_partial_rec.ids
                        else:
                            aml_to_balance.reconcile()
                    exchange_move.post()
                    exchange_move_id = exchange_move.id
                else:
                    missing_exchange_difference = True
            if not missing_exchange_difference:
                #mark the reference of the full reconciliation on the exchange rate entries and on the entries
                self.env['account.full.reconcile'].with_context(check_move_validity=False).create({
                    'partial_reconcile_ids': [(6, 0, partial_rec_ids)],
                    'reconciled_line_ids': [(6, 0, amls.ids)],
                    'exchange_move_id': exchange_move_id,
                })            

    def _check_reconciliation(self):
        moves = self.mapped('move_id')
        for m in moves:
            m.update({'state':'posted'})
        for line in self:
            if line.matched_debit_ids or line.matched_credit_ids:
                line.remove_move_reconcile()     

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []

        if self._context.get('payment_wizard_out'):
            currency_id = self._context.get('currency_id')

            if not currency_id:
                currency_id = False

            args += [('full_reconcile_id', '=', False), 
                ('balance', '!=', 0),
                ('account_id.reconcile', '=', True),
                ('reconciled', '=', False),
                ('in_payment', '=', False),
                ('move_id.type','!=','entry'),
                ('move_id.state', '=', 'posted'),
            ]

        if self._context.get('payment_wizard_in'):
            currency_id = self._context.get('currency_id')

            if not currency_id:
                currency_id = False

            args += [('full_reconcile_id', '=', False), 
                ('balance', '!=', 0),
                ('account_id.reconcile', '=', True),
                ('reconciled', '=', False),
                ('in_payment', '=', False),
                ('move_id.type','!=','entry'),
                ('move_id.state', '=', 'posted'),
            ]

        if self._context.get('partner_id') and self._context.get('partner_type'):
            partner_id = int(self._context.get('partner_id'))
            args = ['|', ('move_id.state', '=', 'posted'), '&', 
                ('move_id.state', '=', 'draft'), 
                ('partner_id', '=', partner_id),
                ('reconciled', '=', False), '|', 
                ('amount_residual', '!=', 0.0),
                ('amount_residual_currency', '!=', 0.0)
            ]

            if self._context.get('partner_type') == 'customer':
                account_ids = self.env['account.account'].search([
                ('company_id', '=', self.env.user.company_id.id),
                ('user_type_id.type', '=', 'receivable')])

                args.extend([('credit', '>', 0), ('debit', '=', 0),
                    ('account_id','in',account_ids.ids or [])])
            else:
                account_ids = self.env['account.account'].search([
                ('company_id', '=', self.env.user.company_id.id),
                ('user_type_id.type', '=', 'payable')])

                args.extend([('credit', '=', 0), ('debit', '>', 0),
                    ('account_id','in',account_ids.ids or [])])

        return super(AccountMoveLineInherit, self)._name_search(name=name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid)


class AccountPartialReconcileInherit(models.Model):
    _inherit = "account.partial.reconcile"

    def unlink(self):
        for reconcile in self:
            if self._context.get('from_js'):
                if reconcile.debit_move_id.move_id.is_inbound():
                    if reconcile.credit_move_id.in_payment:
                        if reconcile.credit_move_id.move_id:
                            current_move_id = reconcile.credit_move_id.move_id
                            move_id = reconcile.debit_move_id.move_id

                            move_curreny = move_id.currency_id
                            payment_currency = current_move_id.currency_id
  
                            payment_id = reconcile.credit_move_id.payment_id

                            credit = reconcile.credit_move_id.credit
                            last_line_number = reconcile.credit_move_id.last_line_number

                            partner_id = reconcile.credit_move_id.partner_id
                            currency_id = reconcile.credit_move_id.currency_id

                            move_name = reconcile.debit_move_id.name
                            current_balance = reconcile.debit_move_id.debit - reconcile.debit_move_id.credit

                            account_id = reconcile.debit_move_id.account_id.id

                            do_payment_move_vals = {}
                            remove_lines = []

                            remove_lines.append(reconcile.credit_move_id.id)

                            result = super(AccountPartialReconcileInherit, self).unlink()

                            if current_move_id.line_ids.filtered(lambda x: not x.in_payment and not x.reconciled and (x.partner_id == partner_id)):
                                for line in current_move_id.line_ids.filtered(lambda x: not x.in_payment and not x.reconciled and (x.partner_id == partner_id)):
                                    if line.credit > 0:
                                        credit += line.credit
                                        remove_lines.append(line.id)


                            current_move_id.with_context(check_move_validity=False).write({
                                'line_ids' : [(2, line) for line in remove_lines]
                            })

                            last_line_number = self.env.user.company_id.last_line_number
                            last_line_number += 1
                            self.env.user.company_id.write({
                                'last_line_number' : last_line_number
                            })

                            if payment_id:
                                if payment_id.currency_id != currency_id:
                                    credit = currency_id._convert(credit, payment_id.currency_id, payment_id.company_id, fields.Date.context_today(self))
                                elif (payment_id.currency_id == currency_id) and (move_id.company_currency_id != currency_id):
                                    credit = move_id.company_currency_id._convert(credit, currency_id, payment_id.company_id, fields.Date.context_today(self))
                                else:
                                    credit = credit

                                do_payment_move_vals = payment_id.with_context(
                                    amount_remain=credit,
                                    last_line_number=last_line_number,
                                    partner_id=partner_id)._prepare_payment_moves()
                            else:
                                if (move_curreny == payment_currency) and (payment_currency != move_id.company_currency_id):
                                    credit = credit
                                    amount_currency = move_id.company_currency_id._convert(credit, move_curreny, move_id.company_id, fields.Date.context_today(self))
                                    currency_id = payment_currency.id
                                elif (move_curreny != payment_currency):
                                    credit = credit
                                    amount_currency = move_curreny._convert(credit, payment_currency, move_id.company_id, fields.Date.context_today(self))
                                    currency_id = payment_currency.id
                                else:
                                    credit = credit
                                    amount_currency = 0.0
                                    currency_id = False

                                do_payment_move_vals = self.with_context(
                                    amount_remain=credit,
                                    amount_currency=amount_currency,
                                    current_balance=current_balance,
                                    currency_id=currency_id,
                                    account_id=account_id,
                                    move_name=move_name,
                                    last_line_number=last_line_number,
                                    partner_id=partner_id)._prepare_payment_moves()


                            if len(do_payment_move_vals) >= 1:
                                current_move_id.with_context(check_move_validity=False).write({
                                    'line_ids' : do_payment_move_vals[0].get('line_ids') or self.env['account.move.line']
                                })


                            return result

                if reconcile.credit_move_id.move_id.is_outbound():
                    if reconcile.debit_move_id.in_payment:
                        if reconcile.debit_move_id.move_id:
                            current_move_id = reconcile.debit_move_id.move_id
                            move_id = reconcile.credit_move_id.move_id

                            move_curreny = move_id.currency_id
                            payment_currency = current_move_id.currency_id

                            payment_id = reconcile.debit_move_id.payment_id
                            partner_id = reconcile.debit_move_id.partner_id

                            debit = reconcile.debit_move_id.debit

                            last_line_number = reconcile.debit_move_id.last_line_number
                            currency_id = reconcile.debit_move_id.move_id.currency_id

                            current_balance = reconcile.credit_move_id.debit - reconcile.credit_move_id.credit

                            account_id = reconcile.credit_move_id.account_id.id
                            move_name = reconcile.credit_move_id.name

                            do_payment_move_vals = {}
                            remove_lines = []

                            remove_lines.append(reconcile.debit_move_id.id)

                            result = super(AccountPartialReconcileInherit, self).unlink()

                            if current_move_id.line_ids.filtered(lambda x: not x.in_payment and not x.reconciled and (x.partner_id == partner_id)):
                                for line in current_move_id.line_ids.filtered(lambda x: not x.in_payment and not x.reconciled and (x.partner_id == partner_id)):
                                    if line.debit > 0 :
                                        debit += line.debit
                                        remove_lines.append(line.id)


                            current_move_id.with_context(check_move_validity=False).write({
                                'line_ids' : [(2, line) for line in remove_lines]
                            })

                            last_line_number = self.env.user.company_id.last_line_number
                            last_line_number += 1
                            self.env.user.company_id.write({
                                'last_line_number' : last_line_number
                            })

                            if payment_id:
                                if payment_id.currency_id != currency_id:
                                    debit = currency_id._convert(debit, payment_id.currency_id, payment_id.company_id, fields.Date.context_today(self))
                                elif (payment_id.currency_id == currency_id) and (move_id.company_currency_id != currency_id):
                                    debit = move_id.company_currency_id._convert(debit, currency_id, payment_id.company_id, fields.Date.context_today(self))
                                else:
                                    debit = debit

                                do_payment_move_vals = payment_id.with_context(
                                    amount_remain=debit,
                                    last_line_number=last_line_number,
                                    partner_id=partner_id)._prepare_payment_moves()
                            else:
                               
                                if (move_curreny == payment_currency) and (payment_currency != move_id.company_currency_id):
                                    debit = debit
                                    amount_currency = move_id.company_currency_id._convert(debit, move_curreny, move_id.company_id, fields.Date.context_today(self))
                                    currency_id = payment_currency.id
                                elif (move_curreny != payment_currency):
                                    debit = debit
                                    amount_currency = move_curreny._convert(debit, payment_currency, move_id.company_id, fields.Date.context_today(self))
                                    currency_id = payment_currency.id
                                else:
                                    debit = debit
                                    amount_currency = 0.0
                                    currency_id = False

                                do_payment_move_vals = self.with_context(
                                    amount_remain=debit,
                                    amount_currency=amount_currency,
                                    current_balance=current_balance,
                                    currency_id=currency_id,
                                    account_id=account_id,
                                    move_name=move_name,
                                    last_line_number=last_line_number,
                                    partner_id=partner_id)._prepare_payment_moves()
                            


                            if len(do_payment_move_vals) >= 1:
                                current_move_id.write({
                                    'line_ids' : do_payment_move_vals[0].get('line_ids') or self.env['account.move.line']
                                })

                            current_move_id.post()

                            return result
        return super(AccountPartialReconcileInherit, self).unlink()




