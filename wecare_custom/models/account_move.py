# -*- coding: utf-8 -*-

from odoo import fields, models,api

class AccountMove(models.Model):
    _inherit = ['account.move']


    def action_post(self):
        for record in self:
            if record.partner_id and record.partner_id.quitar_chars_especial:
                record.name = record.name.replace('-', '').replace('/', '').replace('_', '')
        return super(AccountMove, self).action_post()