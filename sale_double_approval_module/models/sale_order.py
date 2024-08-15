# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('to_approve', 'To Approve'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, tracking=True, default='draft')

    def _approval_needed(self):
        """Returns whether the order qualifies to be approved by the current user"""
        self.ensure_one()
        if self.company_id.so_double_validation:
            return (
                self.user_has_groups('sales_team.group_sale_manager')
                or self.amount_total < self.env.company.currency_id._convert(
                    self.company_id.so_double_validation_amount, self.currency_id, self.company_id,
                    self.date_order or fields.Date.today()
                )
            )
        return False

    def button_approve(self, force=False):
        """Button to approve the record if it is in approve stage by the manager"""
        # Filtrar los registros que no están en estado 'done', 'cancel', o 'sale'
        orders_to_approve = self.filtered(lambda order: order.state not in ['done', 'cancel', 'sale'])

        # Filtrar adicionalmente los que necesitan aprobación
        orders_to_approve = orders_to_approve.filtered(lambda order: order._approval_needed())

        # Solo se ejecuta la lógica si hay registros que aprobar
        if orders_to_approve:
            orders_to_approve.write({
                'state': 'draft',
                'date_order': fields.Datetime.now(),
            })
            orders_to_approve.action_confirm()
        
        return {}

    def action_confirm(self):
        for order in self:
            if order._approval_needed():
                return super(SaleOrderInherit, order).action_confirm()
            else:
                order.update({'state': 'to_approve'})

    def action_refuse(self):
        current = self.filtered(lambda order: order.state == 'to_approve')
        current.write({'state': 'cancel'})
        return True


class ResConfigSettingsInherit(models.TransientModel):
    _inherit = 'res.config.settings'

    sale_order_approval = fields.Boolean("Sale Order Approval", default=lambda self: self.env.company.so_double_validation)
    sale_order_min_amount = fields.Monetary(related='company_id.so_double_validation_amount', string="Minimum Amount")
