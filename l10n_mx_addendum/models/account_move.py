import base64

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    addendum_id = fields.Many2one(
        related="partner_id.addendum_id",
    )
    addendum_manual = fields.Boolean(
        related="partner_id.addendum_id.manual",
    )
    addendum_generated = fields.Boolean(
        copy=False,
    )

    def write_addendum(self, attachment, addendum_content):
        datas_decoded = base64.b64decode(attachment.datas)
        xml_data = datas_decoded.replace(
            b"</cfdi:Comprobante>",
            b"\n" + str.encode(addendum_content) + b"\n</cfdi:Comprobante>",
        )
        attachment.write({"datas": base64.encodebytes(xml_data), "mimetype": "application/xml"})
        self.addendum_generated = True
        return xml_data

    def _get_addendum_content(self, data=None):
        self.ensure_one()
        if not self.addendum_id:
            return ""
        data = dict(data or {})
        template = (
            self.addendum_id.generate(data)
            if self.addendum_id.is_jinja
            else self.addendum_id.raw_template
        )
        addendum_content = template.replace('<?xml version="1.0" encoding="UTF-8"?>\n', "").replace(
            '<?xml version="1.0" encoding="UTF-8"?>', ""
        )
        return addendum_content

    def get_last_modified_attachment(self, name):
        attachment = self.env["ir.attachment"].search(
            [
                ("res_model", "=", self._name),
                ("res_id", "=", self.id),
                ("name", "=like", name),
            ],
            limit=1,
            order="write_date DESC",
        )
        return attachment

    def generate_addendum(self, data=None, attachment=None, raise_if_not_attachment=True):
        self.ensure_one()

        data = dict(data or {})
        if not data.get("o"):
            data["o"] = self

        attachment = attachment or self.get_last_modified_attachment("%.xml")
        if not attachment:
            if raise_if_not_attachment:
                raise ValidationError(_("No XML founded, ensure is generated"))
            return

        addendum_content = self._get_addendum_content(data)
        if addendum_content:
            self.write_addendum(attachment, addendum_content)
