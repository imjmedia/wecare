# Copyright 2023 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import models


class PrintnodeUpgrade(models.TransientModel):
    """
    Wizard with link to PRO version
    """
    _name = 'printnode.upgrade'
    _description = 'Direct Print Upgrade Wizard'
