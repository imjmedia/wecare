from odoo import fields, models


class AccountMoveAddendumFieldValue(models.TransientModel):
    _name = "account.move.addendum.field.value"
    _order = "field_id"
    _description = "Addendum Field/Value"

    field_id = fields.Many2one(
        index=True,
        comodel_name="account.move.addendum.field",
        readonly=True,
    )
    value = fields.Char(
        readonly=False,
    )
