# Copyright 2023 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import models


class PrintnodeWorkstation(models.Model):
    """
    Workstation to set default devices
    """
    _name = 'printnode.workstation'
    _description = 'Printnode Workstation'
