# Copyright 2023 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import models


class PrintNodeScenario(models.Model):
    """
    Scenarios to print reports
    """
    _name = 'printnode.scenario'
    _description = 'PrintNode Scenarios'
