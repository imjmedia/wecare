from odoo import fields, models


class AccountMoveAddendumField(models.Model):
    _name = "account.move.addendum.field"
    _order = "name"
    _description = "Addendum Field"

    name = fields.Char(
        index=True,
        required=True,
    )
    technical_name = fields.Char(
        required=True,
        help="This value will be replaced inside the addendum",
    )
    addendum_id = fields.Many2one(
        string="addendum",
        comodel_name="account.move.addendum",
        ondelete="cascade",
        required=True,
    )
    default_value = fields.Char(
        help="Default value setted in the addendum wizard",
    )
