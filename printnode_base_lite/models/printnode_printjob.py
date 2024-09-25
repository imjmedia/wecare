# Copyright 2023 VentorTech OU
# See LICENSE file for full copyright and licensing details.
from datetime import datetime, timedelta

from odoo import api, models, fields


class PrintNodePrintJob(models.Model):
    """
    PrintNode Job entity
    """
    _name = 'printnode.printjob'
    _description = 'PrintNode Job'

    # Actually, it is enough to have only 20 symbols but to be sure...
    printnode_id = fields.Char(
        string='Direct Print ID',
        size=64,
        default='__New_ID__',
    )

    printer_id = fields.Many2one(
        'printnode.printer',
        string='Printer',
        ondelete='cascade',
    )

    description = fields.Char(
        string='Label',
        size=64
    )

    @api.model
    def create_job(self, title='', printer_id=False, content=None, content_type=None):
        create_vals = {
            'printer_id': printer_id,
            'description': title,
        }
        res = super().create(create_vals)

        return res

    def clean_printjobs(self, older_than_days):
        """
        Remove printjobs older than `older_than` days ago
        """
        days_ago = datetime.now() - timedelta(days=older_than_days)

        printjobs = self.search([('create_date', '<', days_ago)])

        printjobs.unlink()
