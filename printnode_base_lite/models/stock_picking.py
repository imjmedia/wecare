# Copyright 2023 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import models, _


class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = 'stock.picking'

    def print_last_shipping_label(self):
        """
        Print last shipping label if possible.
        """
        # Show Upgrade wizard
        return {
            'name': _('Print Last Shipping Label'),
            'type': 'ir.actions.act_window',
            'res_model': 'printnode.upgrade',
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }
