# Copyright 2023 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class User(models.Model):
    """ User entity. Add 'Default Printer' field (no restrictions).
    """
    _inherit = 'res.users'

    printnode_enabled = fields.Boolean(
        string='Auto-print via Direct Print',
        default=False,
    )

    printnode_printer = fields.Many2one(
        'printnode.printer',
        string='Default Printer',
    )

    @property
    def SELF_READABLE_FIELDS(self):
        readable_fields = [
            'printnode_enabled',
            'printnode_printer',
        ]

        return super().SELF_READABLE_FIELDS + readable_fields

    @property
    def SELF_WRITEABLE_FIELDS(self):
        writable_fields = [
            'printnode_enabled',
            'printnode_printer',
        ]

        return super().SELF_WRITEABLE_FIELDS + writable_fields

    def get_report_printer(self, report_id):
        """
        :param int report_id: ID of the report to searching

        Printer search sequence:
        1. Default printer for current user (User Preferences)
        2. Default printer for current company (Settings)
        """
        self.ensure_one()

        return self.printnode_printer or self.env.company.printnode_printer
