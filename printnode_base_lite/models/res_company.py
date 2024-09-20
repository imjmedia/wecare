# Copyright 2023 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class Company(models.Model):
    _inherit = 'res.company'

    printnode_enabled = fields.Boolean(
        string='Enable Direct Printing',
        default=False,
    )

    printnode_printer = fields.Many2one(
        'printnode.printer',
        string='Printer',
    )

    auto_send_slp = fields.Boolean(
        string='Auto-send to Shipping Label Printer',
        default=False,
    )

    print_sl_from_attachment = fields.Boolean(
        string='Use Attachments Printing for Shipping Label(s)',
        default=False,
    )

    im_a_teapot = fields.Boolean(
        string='Show success notifications',
        default=True,
    )

    print_package_with_label = fields.Boolean(
        string='Print Package just after Shipping Label',
        default=False,
    )

    scales_enabled = fields.Boolean(
        string='Enable Scales Integration',
        default=False,
    )

    printnode_notification_email = fields.Char(
        string="Direct Print Notification Email",
    )

    printnode_notification_page_limit = fields.Integer(
        string="Direct Print Notification Page Limit",
        default=100,
    )

    secure_printing = fields.Boolean(
        string='Printing without sending documents to the print server',
        default=False,
    )
