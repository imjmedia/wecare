from odoo import fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    addendum_id = fields.Many2one(
        comodel_name="account.move.addendum",
    )
