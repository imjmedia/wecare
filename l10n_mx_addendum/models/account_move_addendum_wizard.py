from odoo import fields, models


class AccountMoveAddendumWizard(models.TransientModel):
    _name = "account.move.addendum.wizard"
    _description = "Addendum Wizard"

    def _get_move_id(self):
        return self.env["account.move"].browse(self._context.get("active_id"))

    def compute_field_value_ids(self):
        move = self.move_id or self._get_move_id()
        return self.env["account.move.addendum.field.value"].create(
            [
                {
                    "field_id": field.id,
                    "value": field.default_value,
                }
                for field in move.partner_id.addendum_id.field_ids
            ]
        )

    move_id = fields.Many2one(
        comodel_name="account.move",
        default=_get_move_id,
        readonly=True,
    )
    field_value_ids = fields.Many2many(
        string="fields",
        comodel_name="account.move.addendum.field.value",
        relation="move_field_value_rel",
        default=compute_field_value_ids,
    )

    def generate_addendum_manual(self):
        self.ensure_one()
        data = {fv.field_id.technical_name: fv.value for fv in self.field_value_ids}
        self.move_id.generate_addendum(data)
