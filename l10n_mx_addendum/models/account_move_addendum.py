import xml

import jinja2

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountMoveAddendum(models.Model):
    _name = "account.move.addendum"
    _description = "Addendum"

    name = fields.Char(
        required=True,
        index=True,
    )
    manual = fields.Boolean(
        help="Mark as `True` to create the Addendum manually instead o automatically in the generation of XML."
    )
    is_jinja = fields.Boolean(
        default=True,
        help="Mark as `True` if the Addendum is dynamic, use Jinja to create the template.",
    )
    raw_template = fields.Text(
        help="Addendum template to be use in the XML generation.",
    )
    template_internal = fields.Char(
        inverse="_inverse_template_internal",
        readonly=True,
    )
    field_ids = fields.One2many(
        comodel_name="account.move.addendum.field",
        inverse_name="addendum_id",
    )

    def _inverse_template_internal(self):
        for addendum in self:
            if addendum.raw_template:
                return
            addendum.reload_from_file()

    def reload_from_file(self):
        if self.template_internal:
            self.raw_template = self.env.ref(self.template_internal).render()
            self.raw_template = (
                self.raw_template.replace("<Addenda", "<cfdi:Addenda")
                .replace("</Addenda>", "</cfdi:Addenda>")
                .replace("\n    ", "\n")  # Remove spaces generated from <odoo> & <template> tags
            )[1:]

    @api.constrains("raw_template")
    def validate_addendum(self):
        """Checks the integrity of the Addendum Template

        Raises:
            ValidationError: If the addendum has invalid content
        """
        for addendum in self:
            if not addendum.raw_template:
                continue
            if addendum.is_jinja:
                try:
                    jinja2.Template(addendum.raw_template)
                except jinja2.TemplateSyntaxError:
                    raise ValidationError(_("Invalid Jinja template"))
            else:
                try:
                    xml.dom.minidom.parseString(addendum.raw_template)
                except xml.parsers.expat.ExpatError:
                    raise ValidationError(_("Invalid XML template"))

    def generate(self, args):
        try:
            template = jinja2.Template(self.raw_template, trim_blocks=True, lstrip_blocks=True)
            render = template.render(**args)
        except jinja2.TemplateSyntaxError:
            raise ValidationError(_("Invalid Jinja template"))
        except jinja2.UndefinedError:
            raise ValidationError(_("Invalid Jinja structure"))
        return render
