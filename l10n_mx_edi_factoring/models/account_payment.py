# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, fields


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    l10n_mx_edi_factoring_id = fields.Many2one(
        "res.partner", "Financial Factor", copy=False,
        help="This payment was received from this factoring.")

    @api.model
    def default_get(self, fields_list):
        rec = super(AccountPayment, self).default_get(fields_list)
        active_ids = self._context.get('active_ids') or self._context.get(
            'active_id')
        active_model = self._context.get('active_model')

        # Check for selected invoices ids
        if not active_ids or active_model != 'account.move':
            return rec

        invoices = self.env['account.move'].browse(active_ids).filtered(
            lambda move: move.is_invoice(include_receipts=True) and
            move.l10n_mx_edi_cfdi_request == 'on_invoice')
        if not invoices:
            return rec
        # If come from an unique invoice nothing to special to set,
        # the factoring will be the one in the partner if set.
        factoring = invoices[0].l10n_mx_edi_factoring_id
        if not factoring and rec.get('partner_id'):
            factoring = self.env['res.partner'].browse(rec.get(
                'partner_id')).l10n_mx_edi_factoring_id
        rec['l10n_mx_edi_factoring_id'] = factoring.id
        return rec

    def action_post(self):
        """Assign the factoring in the invoices related"""
        for record in self.filtered(lambda r: r.l10n_mx_edi_cfdi_request == 'on_payment'):
            record.reconciled_invoice_ids.write({
                'l10n_mx_edi_factoring_id': record.l10n_mx_edi_factoring_id.id,
            })
        return super(AccountPayment, self).action_post()


class AccountRegisterPayments(models.TransientModel):
    _inherit = "account.payment.register"

    l10n_mx_edi_factoring_id = fields.Many2one(
        "res.partner", "Financial Factor", copy=False,
        help="This payment was received from this factoring.")

    @api.model
    def default_get(self, fields_list):
        rec = super(AccountRegisterPayments, self).default_get(fields_list)
        active_ids = self._context.get('active_ids')
        model = self._context.get('active_model')
        if model != 'account.move' or not active_ids:
            return rec
        # If come from an unique invoice nothing to special to set,
        # the factoring will be the one in the partner if set.
        invoice = self.env['account.move'].browse(active_ids)
        if not invoice.filtered(lambda i: i.l10n_mx_edi_cfdi_request == 'on_invoice'):
            return rec
        factoring = invoice.mapped('l10n_mx_edi_factoring_id').ids
        if not factoring and rec.get('partner_id'):
            factoring = self.env['res.partner'].browse(rec.get(
                'partner_id')).l10n_mx_edi_factoring_id.ids
        rec['l10n_mx_edi_factoring_id'] = factoring[0] if factoring else ''
        return rec

    def _create_payment_vals_from_wizard(self):
        res = super(AccountRegisterPayments, self)._create_payment_vals_from_wizard()
        res['l10n_mx_edi_factoring_id'] = self.l10n_mx_edi_factoring_id.id
        return res
