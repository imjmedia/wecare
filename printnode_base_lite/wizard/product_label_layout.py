# Copyright 2023 VentorTech OU
# See LICENSE file for full copyright and licensing details.

from odoo import models


class ProductLabelLayout(models.TransientModel):
    _inherit = 'product.label.layout'

    def process(self):
        return super(ProductLabelLayout, self.with_context(download_only=True)).process()
