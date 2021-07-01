# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,api, _


class account_payment(models.TransientModel):
    _inherit ='account.payment.register'

    @api.onchange('tipo_de_cambio')
    def cambio(self):
        self.manual_currency_rate = 0
        if self.tipo_de_cambio:
            self.manual_currency_rate = (1 / self.tipo_de_cambio)

    manual_currency_rate_active = fields.Boolean('¿Tipo de Cambio Manual?', store=True)
    manual_currency_rate = fields.Float(string='Tarifa', digits=(12,6), compute='cambio')
    tipo_de_cambio = fields.Float(string="Tipo de Cambio", digits=(12,2), default=0.0)

    @api.model
    def default_get(self, default_fields):
        rec = super(account_payment, self).default_get(default_fields)
        active_ids = self._context.get('active_ids') or self._context.get('active_id')
        active_model = self._context.get('active_model')

        # Check for selected invoices ids
        if not active_ids or active_model != 'account.move':
            return rec
        invoices = self.env['account.move'].browse(active_ids).filtered(lambda move: move.is_invoice(include_receipts=True))
        rec.update({
            'manual_currency_rate_active':invoices.manual_currency_rate_active,
            'manual_currency_rate':invoices.manual_currency_rate
            })
        return rec



    @api.depends('source_amount', 'source_amount_currency', 'source_currency_id', 'company_id', 'currency_id', 'payment_date', 'manual_currency_rate')
    def _compute_amount(self):
        for wizard in self:
            if wizard.source_currency_id == wizard.currency_id:
                # Same currency.
                wizard.amount = wizard.source_amount_currency
            elif wizard.currency_id == wizard.company_id.currency_id:
                # Payment expressed on the company's currency.
                wizard.amount = wizard.source_amount
            else:
                # Foreign currency on payment different than the one set on the journal entries.
                amount_payment_currency = wizard.company_id.currency_id._convert(wizard.source_amount, wizard.currency_id, wizard.company_id, wizard.payment_date)
                wizard.amount = amount_payment_currency

    @api.depends('amount')
    def _compute_payment_difference(self):
        for wizard in self:
            if wizard.source_currency_id == wizard.currency_id:
                # Same currency.
                wizard.payment_difference = wizard.source_amount_currency - wizard.amount
            elif wizard.currency_id == wizard.company_id.currency_id:
                # Payment expressed on the company's currency.
                wizard.payment_difference = wizard.source_amount - wizard.amount
            else:
                # Foreign currency on payment different than the one set on the journal entries.
                amount_payment_currency = wizard.company_id.currency_id._convert(wizard.source_amount, wizard.currency_id, wizard.company_id, wizard.payment_date)
                wizard.payment_difference = amount_payment_currency - wizard.amount


    def _create_payment_vals_from_wizard(self):
        res = super(account_payment, self)._create_payment_vals_from_wizard()
        if self.manual_currency_rate_active:
            res.update({'manual_currency_rate_active': self.manual_currency_rate_active, 'manual_currency_rate': self.manual_currency_rate})
        return res




class AccountPayment(models.Model):
    _inherit = "account.payment"
    _description = "Payments"

    @api.onchange('tipo_de_cambio')
    def cambio(self):
        if self.tipo_de_cambio:
            self.manual_currency_rate = (1/self.tipo_de_cambio)

    manual_currency_rate_active = fields.Boolean('¿Tipo de Cambio Manual?', store=True)
    manual_currency_rate = fields.Float(string='Tarifa', digits=(12,6), compute='cambio')
    tipo_de_cambio = fields.Float(string="Tipo de Cambio", digits=(12, 2))

    @api.model
    def default_get(self, default_fields):
        rec = super(AccountPayment, self).default_get(default_fields)
        active_ids = self._context.get('active_ids') or self._context.get('active_id')
        active_model = self._context.get('active_model')

        # Check for selected invoices ids
        if not active_ids or active_model != 'account.move':
            return rec
        invoices = self.env['account.move'].browse(active_ids).filtered(
            lambda move: move.is_invoice(include_receipts=True))
        rec.update({
            'manual_currency_rate_active': invoices.manual_currency_rate_active,
            'manual_currency_rate': invoices.manual_currency_rate
        })
        return rec

    @api.model
    def _compute_payment_amount(self, invoices, currency, journal, date):
        '''Compute the total amount for the payment wizard.
        :param invoices:    Invoices on which compute the total as an account.invoice recordset.
        :param currency:    The payment's currency as a res.currency record.
        :param journal:     The payment's journal as an account.journal record.
        :param date:        The payment's date as a datetime.date object.
        :return:            The total amount to pay the invoices.
        '''
        company = journal.company_id
        currency = currency or journal.currency_id or company.currency_id
        date = date or fields.Date.today()

        if not invoices:
            return 0.0

        self.env['account.move'].flush(['type', 'currency_id'])
        self.env['account.move.line'].flush(['amount_residual', 'amount_residual_currency', 'move_id', 'account_id'])
        self.env['account.account'].flush(['user_type_id'])
        self.env['account.account.type'].flush(['type'])
        self._cr.execute('''
                SELECT
                    move.type AS type,
                    move.currency_id AS currency_id,
                    SUM(line.amount_residual) AS amount_residual,
                    SUM(line.amount_residual_currency) AS residual_currency
                FROM account_move move
                LEFT JOIN account_move_line line ON line.move_id = move.id
                LEFT JOIN account_account account ON account.id = line.account_id
                LEFT JOIN account_account_type account_type ON account_type.id = account.user_type_id
                WHERE move.id IN %s
                AND account_type.type IN ('receivable', 'payable')
                GROUP BY move.id, move.type
            ''', [tuple(invoices.ids)])
        query_res = self._cr.dictfetchall()

        total = 0.0
        for inv in invoices:
            for res in query_res:
                move_currency = self.env['res.currency'].browse(res['currency_id'])
                if move_currency == currency and move_currency != company.currency_id:
                    total += res['residual_currency']
                else:
                    if not inv.manual_currency_rate_active:
                        total += company.currency_id._convert(res['amount_residual'], currency, company, date)
                    else:
                        total += res['residual_currency'] * inv.manual_currency_rate
        return total

    @api.depends('invoice_ids', 'amount', 'payment_date', 'currency_id', 'payment_type', 'manual_currency_rate')
    def _compute_payment_difference(self):
        draft_payments = self.filtered(lambda p: p.invoice_ids and p.state == 'draft')
        for pay in draft_payments:
            payment_amount = -pay.amount if pay.payment_type == 'outbound' else pay.amount
            pay.payment_difference = pay._compute_payment_amount(pay.invoice_ids, pay.currency_id, pay.journal_id,
                                                                 pay.payment_date) - payment_amount
        (self - draft_payments).payment_difference = 0

    def _prepare_payment_moves(self):
        ''' Prepare the creation of journal entries (account.move) by creating a list of python dictionary to be passed
        to the 'create' method.

        Example 1: outbound with write-off:

        Account             | Debit     | Credit
        ---------------------------------------------------------
        BANK                |   900.0   |
        RECEIVABLE          |           |   1000.0
        WRITE-OFF ACCOUNT   |   100.0   |

        Example 2: internal transfer from BANK to CASH:

        Account             | Debit     | Credit
        ---------------------------------------------------------
        BANK                |           |   1000.0
        TRANSFER            |   1000.0  |
        CASH                |   1000.0  |
        TRANSFER            |           |   1000.0

        :return: A list of Python dictionary to be passed to env['account.move'].create.
        '''
        all_move_vals = []
        for payment in self:
            company_currency = payment.company_id.currency_id
            move_names = payment.move_name.split(
                payment._get_move_name_transfer_separator()) if payment.move_name else None

            # Compute amounts.
            write_off_amount = payment.payment_difference_handling == 'reconcile' and -payment.payment_difference or 0.0
            if payment.payment_type in ('outbound', 'transfer'):
                counterpart_amount = payment.amount
                liquidity_line_account = payment.journal_id.default_debit_account_id
            else:
                counterpart_amount = -payment.amount
                liquidity_line_account = payment.journal_id.default_credit_account_id
            # Manage currency.
            if payment.currency_id == company_currency:
                # Single-currency.
                balance = counterpart_amount
                write_off_balance = write_off_amount
                counterpart_amount = write_off_amount = 0.0
                currency_id = False
            else:
                # Multi-currencies.
                if payment.manual_currency_rate_active:
                    balance = counterpart_amount / payment.manual_currency_rate
                    write_off_balance = write_off_amount / payment.manual_currency_rate
                    currency_id = payment.currency_id.id
                else:
                    balance = payment.currency_id._convert(counterpart_amount, company_currency, payment.company_id,
                                                           payment.payment_date)
                    write_off_balance = payment.currency_id._convert(write_off_amount, company_currency,
                                                                     payment.company_id, payment.payment_date)
                    currency_id = payment.currency_id.id

            # Manage custom currency on journal for liquidity line.
            if payment.journal_id.currency_id and payment.currency_id != payment.journal_id.currency_id:
                # Custom currency on journal.
                liquidity_line_currency_id = payment.journal_id.currency_id.id
                liquidity_amount = company_currency._convert(
                    balance, payment.journal_id.currency_id, payment.company_id, payment.payment_date)
            else:
                # Use the payment currency.
                liquidity_line_currency_id = currency_id
                liquidity_amount = counterpart_amount
            # Compute 'name' to be used in receivable/payable line.
            rec_pay_line_name = ''
            if payment.payment_type == 'transfer':
                rec_pay_line_name = payment.name
            else:
                if payment.partner_type == 'customer':
                    if payment.payment_type == 'inbound':
                        rec_pay_line_name += _("Customer Payment")
                    elif payment.payment_type == 'outbound':
                        rec_pay_line_name += _("Customer Credit Note")
                elif payment.partner_type == 'supplier':
                    if payment.payment_type == 'inbound':
                        rec_pay_line_name += _("Vendor Credit Note")
                    elif payment.payment_type == 'outbound':
                        rec_pay_line_name += _("Vendor Payment")
                if payment.invoice_ids:
                    rec_pay_line_name += ': %s' % ', '.join(payment.invoice_ids.mapped('name'))

            # Compute 'name' to be used in liquidity line.
            if payment.payment_type == 'transfer':
                liquidity_line_name = _('Transfer to %s') % payment.destination_journal_id.name
            else:
                liquidity_line_name = payment.name

            # ==== 'inbound' / 'outbound' ====
            move_vals = {
                'date': payment.payment_date,
                'ref': payment.communication,
                'manual_currency_rate': payment.manual_currency_rate,
                'manual_currency_rate_active': payment.manual_currency_rate_active,
                'journal_id': payment.journal_id.id,
                'currency_id': payment.journal_id.currency_id.id or payment.company_id.currency_id.id,
                'partner_id': payment.partner_id.id,
                'line_ids': [
                    # Receivable / Payable / Transfer line.
                    (0, 0, {
                        'name': rec_pay_line_name,
                        'amount_currency': counterpart_amount + write_off_amount,
                        'currency_id': currency_id,
                        'debit': balance + write_off_balance > 0.0 and balance + write_off_balance or 0.0,
                        'credit': balance + write_off_balance < 0.0 and -balance - write_off_balance or 0.0,
                        'date_maturity': payment.payment_date,
                        'partner_id': payment.partner_id.id,
                        'account_id': payment.destination_account_id.id,
                        'payment_id': payment.id,
                    }),
                    # Liquidity line.
                    (0, 0, {
                        'name': liquidity_line_name,
                        'amount_currency': -liquidity_amount,
                        'currency_id': liquidity_line_currency_id,
                        'debit': balance < 0.0 and -balance or 0.0,
                        'credit': balance > 0.0 and balance or 0.0,
                        'date_maturity': payment.payment_date,
                        'partner_id': payment.partner_id.id,
                        'account_id': liquidity_line_account.id,
                        'payment_id': payment.id,
                    }),
                ],
            }
            if write_off_balance:
                # Write-off line.
                move_vals['line_ids'].append((0, 0, {
                    'name': payment.writeoff_label,
                    'amount_currency': -write_off_amount,
                    'currency_id': currency_id,
                    'debit': write_off_balance < 0.0 and -write_off_balance or 0.0,
                    'credit': write_off_balance > 0.0 and write_off_balance or 0.0,
                    'date_maturity': payment.payment_date,
                    'partner_id': payment.partner_id.id,
                    'account_id': payment.writeoff_account_id.id,
                    'payment_id': payment.id,
                }))

            if move_names:
                move_vals['name'] = move_names[0]

            all_move_vals.append(move_vals)

            # ==== 'transfer' ====
            if payment.payment_type == 'transfer':

                if payment.destination_journal_id.currency_id:
                    transfer_amount = payment.currency_id._convert(counterpart_amount,
                                                                   payment.destination_journal_id.currency_id,
                                                                   payment.company_id, payment.payment_date)
                else:
                    transfer_amount = 0.0

                transfer_move_vals = {
                    'date': payment.payment_date,
                    'ref': payment.communication,
                    'manual_currency_rate': payment.manual_currency_rate,
                    'manual_currency_rate_active': payment.manual_currency_rate_active,
                    'partner_id': payment.partner_id.id,
                    'journal_id': payment.destination_journal_id.id,
                    'line_ids': [
                        # Transfer debit line.
                        (0, 0, {
                            'name': payment.name,
                            'amount_currency': -counterpart_amount,
                            'currency_id': currency_id,
                            'debit': balance < 0.0 and -balance or 0.0,
                            'credit': balance > 0.0 and balance or 0.0,
                            'date_maturity': payment.payment_date,
                            'partner_id': payment.partner_id.id,
                            'account_id': payment.company_id.transfer_account_id.id,
                            'payment_id': payment.id,
                        }),
                        # Liquidity credit line.
                        (0, 0, {
                            'name': _('Transfer from %s') % payment.journal_id.name,
                            'amount_currency': transfer_amount,
                            'currency_id': payment.destination_journal_id.currency_id.id,
                            'debit': balance > 0.0 and balance or 0.0,
                            'credit': balance < 0.0 and -balance or 0.0,
                            'date_maturity': payment.payment_date,
                            'partner_id': payment.partner_id.id,
                            'account_id': payment.destination_journal_id.default_credit_account_id.id,
                            'payment_id': payment.id,
                        }),
                    ],
                }

                if move_names and len(move_names) == 2:
                    transfer_move_vals['name'] = move_names[1]

                all_move_vals.append(transfer_move_vals)

        return all_move_vals

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        ''' Prepare the dictionary to create the default account.move.lines for the current payment.
        :param write_off_line_vals: Optional dictionary to create a write-off account.move.line easily containing:
            * amount:       The amount to be added to the counterpart amount.
            * name:         The label to set on the line.
            * account_id:   The account on which create the write-off.
        :return: A list of python dictionary to be passed to the account.move.line's 'create' method.
        '''
        self.ensure_one()
        write_off_line_vals = write_off_line_vals or {}

        if not self.journal_id.payment_debit_account_id or not self.journal_id.payment_credit_account_id:
            raise UserError(_(
                "You can't create a new payment without an outstanding payments/receipts accounts set on the %s journal."
            ) % self.journal_id.display_name)

        # Compute amounts.
        write_off_amount = write_off_line_vals.get('amount', 0.0)

        if self.payment_type == 'inbound':
            # Receive money.
            counterpart_amount = -self.amount
            write_off_amount *= -1
        elif self.payment_type == 'outbound':
            # Send money.
            counterpart_amount = self.amount
        else:
            counterpart_amount = 0.0
            write_off_amount = 0.0


        if self.manual_currency_rate_active:
            balance = counterpart_amount / self.manual_currency_rate
            counterpart_amount_currency = counterpart_amount
            write_off_balance = write_off_amount / self.manual_currency_rate
            write_off_amount_currency = write_off_amount
            currency_id = self.currency_id.id
        
        else:
            balance = self.currency_id._convert(counterpart_amount, self.company_id.currency_id, self.company_id, self.date)
            counterpart_amount_currency = counterpart_amount
            write_off_balance = self.currency_id._convert(write_off_amount, self.company_id.currency_id, self.company_id, self.date)
            write_off_amount_currency = write_off_amount
            currency_id = self.currency_id.id

        if self.is_internal_transfer:
            if self.payment_type == 'inbound':
                liquidity_line_name = _('Transfer to %s', self.journal_id.name)
            else: # payment.payment_type == 'outbound':
                liquidity_line_name = _('Transfer from %s', self.journal_id.name)
        else:
            liquidity_line_name = self.payment_reference

        # Compute a default label to set on the journal items.

        payment_display_name = {
            'outbound-customer': _("Customer Reimbursement"),
            'inbound-customer': _("Customer Payment"),
            'outbound-supplier': _("Vendor Payment"),
            'inbound-supplier': _("Vendor Reimbursement"),
        }

        default_line_name = self.env['account.move.line']._get_default_line_name(
            payment_display_name['%s-%s' % (self.payment_type, self.partner_type)],
            self.amount,
            self.currency_id,
            self.date,
            partner=self.partner_id,
        )

        line_vals_list = [
            # Liquidity line.
            {
                'name': liquidity_line_name or default_line_name,
                'date_maturity': self.date,
                'amount_currency': -counterpart_amount_currency,
                'currency_id': currency_id,
                'debit': balance < 0.0 and -balance or 0.0,
                'credit': balance > 0.0 and balance or 0.0,
                'partner_id': self.partner_id.id,
                'account_id': self.journal_id.payment_debit_account_id.id if balance < 0.0 else self.journal_id.payment_credit_account_id.id,
            },
            # Receivable / Payable.
            {
                'name': self.payment_reference or default_line_name,
                'date_maturity': self.date,
                'amount_currency': counterpart_amount_currency + write_off_amount_currency if currency_id else 0.0,
                'currency_id': currency_id,
                'debit': balance + write_off_balance > 0.0 and balance + write_off_balance or 0.0,
                'credit': balance + write_off_balance < 0.0 and -balance - write_off_balance or 0.0,
                'partner_id': self.partner_id.id,
                'account_id': self.destination_account_id.id,
            },
        ]
        if write_off_balance:
            # Write-off line.
            line_vals_list.append({
                'name': write_off_line_vals.get('name') or default_line_name,
                'amount_currency': -write_off_amount_currency,
                'currency_id': currency_id,
                'debit': write_off_balance < 0.0 and -write_off_balance or 0.0,
                'credit': write_off_balance > 0.0 and write_off_balance or 0.0,
                'partner_id': self.partner_id.id,
                'account_id': write_off_line_vals.get('account_id'),
            })
        return line_vals_list

    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
