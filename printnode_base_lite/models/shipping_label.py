# Copyright 2023 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import models


class ShippingLabel(models.Model):
    """
    Shipping Label entity from Delivery Carrier
    """
    _name = 'shipping.label'
    _description = 'Shipping Label'
