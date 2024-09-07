# -*- coding: utf-8 -*-

from odoo import fields, models,api

class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    @api.depends_context('company') #test
    def _credit_debit_get(self):
        if not self.ids:
            self.debit = False
            self.credit = False
            return
        return super(ResPartner, self)._credit_debit_get()