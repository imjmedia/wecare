# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import AccessDenied


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    amount_due = fields.Monetary(related='partner_id.amount_due', currency_field='company_currency_id')
    company_currency_id = fields.Many2one(string='Moneda de Empresa', readonly=True,
        related='company_id.currency_id')

    def action_confirm(self):
        '''
        Check the partner credit limit and exisiting due of the partner
        before confirming the order. The order is only blocked if exisitng
        due is greater than blocking limit of the partner.
        '''
        partner_id = self.partner_id
        total_amount = self.amount_due
        if partner_id.credit_check:
            existing_move = self.env['account.move'].search(
                [('partner_id', '=', self.partner_id.id), ('state', '=', 'posted')])
            if partner_id.credit_blocking <= total_amount and not existing_move:
                view_id = self.env.ref('ob_customer_credit_limit.view_warning_wizard_form')
                context = dict(self.env.context or {})
                context['message'] = "Se excedió el límite de bloqueo de clientes sin tener una cuenta por cobrar, Desea Continuar?"
                context['default_sale_id'] = self.id
                if not self._context.get('warning'):
                    return {
                        'name': 'Warning',
                        'type': 'ir.actions.act_window',
                        'view_mode': 'form',
                        'res_model': 'warning.wizard',
                        'view_id': view_id.id,
                        'target': 'new',
                        'context': context,
                    }
            elif partner_id.credit_warning <= total_amount and partner_id.credit_blocking > total_amount:
                view_id = self.env.ref('ob_customer_credit_limit.view_warning_wizard_form')
                context = dict(self.env.context or {})
                context['message'] = "Monto de Credito excedido, desea continuar?"
                context['default_sale_id'] = self.id
                if not self._context.get('warning'):
                    return {
                        'name': 'Warning',
                        'type': 'ir.actions.act_window',
                        'view_mode': 'form',
                        'res_model': 'warning.wizard',
                        'view_id': view_id.id,
                        'target': 'new',
                        'context': context,
                    }
            elif partner_id.credit_blocking <= total_amount:
                raise AccessDenied(_('Limite de Crédito de Cliente Excedido.'))
        res = super(SaleOrder, self).action_confirm()
        return res
