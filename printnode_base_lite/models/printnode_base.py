# Copyright 2023 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import api, models, _


class PrintnodeBase(models.AbstractModel):
    _name = 'printnode.base'
    _description = 'Printnode Base'

    @api.model
    def get_status(self, only_releases=False):
        """
        Returns all data for status menu.
        """
        if only_releases:
            return {
                'limits': [],
                'devices': {},
            }

        return {
            'limits': self.env['printnode.account'].get_limits(),
            'devices': [
                ('user', self._get_user_devices(),),
                ('company', self._get_company_devices(),),
            ],
        }

    def _get_user_devices(self):
        """
        Returns all devices for current user.
        """
        return [
            {
                'label': _('Default User Printer'),
                'id': self.env.user.printnode_printer.id,
                'name': self.env.user.printnode_printer.name,
            },
        ]

    def _get_company_devices(self):
        """
        Returns all devices for current company.
        """
        return [
            {
                'label': _('Default Company Printer'),
                'id': self.env.company.printnode_printer.id,
                'name': self.env.company.printnode_printer.name,
            },
        ]
