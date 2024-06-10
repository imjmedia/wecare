# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    credit_check = fields.Boolean('Activar Credito', help='Activa el límite de Crédito')
    credit_warning = fields.Monetary('Monto de Advertencia')
    credit_blocking = fields.Monetary('Monto de Bloqueo')
    amount_due = fields.Monetary('Monto a Deber', compute='_compute_amount_due')

    @api.depends('credit', 'debit')
    def _compute_amount_due(self):
        for rec in self:
            rec.amount_due = rec.credit - rec.debit

    @api.constrains('credit_warning', 'credit_blocking')
    def _check_credit_amount(self):
        for credit in self:
            if credit.credit_warning > credit.credit_blocking:
                raise ValidationError(_('Monto de Advertencia no puede ser mayor a monto de bloqueo.'))
            if credit.credit_warning < 0 or credit.credit_blocking < 0:
                raise ValidationError(_('Monto de Advertencia y Monto de Bloqueo no puede ser menor a cero.'))
