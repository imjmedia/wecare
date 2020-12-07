from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self):
        res = super(AccountMove, self).action_post()
        if self.type in ("out_invoice", "out_refund") and not self.addendum_id.manual:
            self.generate_addendum(raise_if_not_attachment=False)
        return res
