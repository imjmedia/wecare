# Copyright 2023 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import exceptions, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    printnode_enabled = fields.Boolean(
        readonly=False,
        related='company_id.printnode_enabled',
    )

    printnode_printer = fields.Many2one(
        'printnode.printer',
        readonly=False,
        related='company_id.printnode_printer',
    )

    auto_send_slp = fields.Boolean(
        readonly=False,
        related='company_id.auto_send_slp',
    )

    print_sl_from_attachment = fields.Boolean(
        readonly=False,
        related='company_id.print_sl_from_attachment',
    )

    im_a_teapot = fields.Boolean(
        readonly=False,
        related='company_id.im_a_teapot',
    )

    print_package_with_label = fields.Boolean(
        readonly=False,
        related='company_id.print_package_with_label',
    )

    scales_enabled = fields.Boolean(
        readonly=False,
        related='company_id.scales_enabled',
    )

    printnode_notification_email = fields.Char(
        readonly=False,
        related='company_id.printnode_notification_email',
    )

    printnode_notification_page_limit = fields.Integer(
        readonly=False,
        related='company_id.printnode_notification_page_limit',
    )

    printnode_account_id = fields.Many2one(
        comodel_name='printnode.account',
        default=lambda self: self.get_main_printnode_account()
    )

    dpc_api_key = fields.Char(
        string='DPC API Key',
        related='printnode_account_id.api_key',
        readonly=False,
    )

    dpc_status = fields.Char(
        string='Direct Print Client API Key Status',
        related='printnode_account_id.status',
    )

    secure_printing = fields.Boolean(
        readonly=False,
        related='company_id.secure_printing',
    )

    # Buttons

    # TODO: Perhaps this concept should be reconsidered, because there can be two or more
    #  accounts. In this case, actions like ('activate_account', 'import_devices',
    #  'clear_devices_from_odoo', ...) must be performed not for the main account with
    #  index [0], but for the account that is selected in the "dpc_api_key" field!
    def get_main_printnode_account(self):
        return self.env['printnode.account'].get_main_printnode_account()

    def activate_account(self):
        """
        Callback for activate button. Finds and activates the main account
        """
        account = self.get_main_printnode_account()

        if not account:
            raise exceptions.UserError(_('Please, add an account before activation'))

        return account.activate_account()

    def import_devices(self):
        """ Import Printers & Scales button in Settings.
        """
        account = self.get_main_printnode_account()

        if not account:
            raise exceptions.UserError(_('Please, add an account before importing printers'))

        return account.import_devices()

    def clear_devices_from_odoo(self):
        """ Callback for "Clear Devices from Odoo" button.
        """
        account = self.get_main_printnode_account()

        if not account:
            raise exceptions.UserError(_('Please, add an account before clearing devices'))

        return account.clear_devices_from_odoo()
