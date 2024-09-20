# Copyright 2023 VentorTech OU
# See LICENSE file for full copyright and licensing details.

import requests

from odoo import api, fields, models, _
from odoo.exceptions import UserError


REQUIRED_REPORT_KEYS = ['title', 'type']


class PrintNodePrinter(models.Model):
    """
    PrintNode Printer entity
    """
    _name = 'printnode.printer'
    _description = 'PrintNode Printer'

    printnode_id = fields.Integer('Direct Print ID')

    active = fields.Boolean(
        'Active',
        default=True
    )

    online = fields.Boolean(
        string='Online',
        compute='_compute_printer_status',
        store=True,
        readonly=True
    )

    name = fields.Char(
        'Name',
        size=64,
        required=True
    )

    status = fields.Char(
        'PrintNode Status',
        size=64
    )

    printjob_ids = fields.One2many(
        'printnode.printjob', 'printer_id',
        string='Print Jobs'
    )

    computer_id = fields.Many2one(
        'printnode.computer',
        string='Computer',
        ondelete='cascade',
        required=True,
    )

    account_id = fields.Many2one(
        'printnode.account',
        string='Account',
        readonly=True,
        related='computer_id.account_id',
        ondelete='cascade',
    )

    _sql_constraints = [
        (
            'printnode_id',
            'unique(printnode_id)',
            'Printer ID should be unique.'
        ),
    ]

    @api.depends('status', 'computer_id.status')
    def _compute_printer_status(self):
        """ check computer and printer status
        """
        for rec in self:
            rec.online = rec.status in ['online'] and \
                rec.computer_id.status in ['connected']

    @api.depends('name', 'computer_id.name')
    def _compute_display_name(self):
        for printer in self:
            printer.display_name = f'{printer.name} ({printer.computer_id.name})'

    def printnode_print_b64(self, ascii_data, params):
        """
        This method is for preparing data for the "qweb-pdf" and "py3o" ("pdf_base64") report types
        before sending it to the Printnode API. Used for printing via Actions -> Print, as well
        as for printing attachments, etc.
        """
        self.ensure_one()

        if not self.env.company.printnode_enabled or not self.env.user.printnode_enabled:
            raise UserError(_(
                'Immediate printing via Direct Print is disabled for company %(company)s. '
                'or current user. Please, contact Administrator to re-enable it.',
                company=self.env.company.name,
            ))

        printnode_data = {
            'printerId': self.printnode_id,
            'qty': params.get('copies', 1),
            'title': params.get('title'),
            'source': self._get_source_name(),
            'contentType': self._get_content_type(params.get('type')),
            'content': ascii_data,
            'options': self._get_data_options(params.get('options', {})),
        }
        return self._post_printnode_job(printnode_data)

    def _create_printnode_job(self, data) -> int:
        """
        Create a new printnode job with the provided data.

        :param data:            A dict of attrs of the request to create printjobs to the Printnode.
        :return:                ID (int) of the created printjob.
        """
        title = data.get('title')
        printer_id = self.id
        content = data.get('content')
        content_type = data.get('contentType')

        printjob_id = None

        printjob_id = self.env['printnode.printjob'].sudo().create_job(
            title, printer_id, content, content_type).id

        return printjob_id

    def _post_printnode_job(self, data):
        """
        Send job into PrintNode. Return new job ID

        :param uri:     The Printnode URI to post printjobs.
        :param data:    A dict of attrs of the request to create printjobs to the Printnode.
                        This should contain the attributes needed by the PrintNode API to process
                        the printjob, such as: 'printerId', 'qty', 'title', 'source', 'contentType',
                        'content'.
        :return:        The printjob ID.
        """
        # Instance ID (int) of 'printnode.printjob' model
        printjob_id = self._create_printnode_job(data)

        # Job ID from PrintNode API
        job_id = False

        auth = requests.auth.HTTPBasicAuth(
            self.account_id.api_key,
            self.account_id.password or ''
        )

        post_url = f'{self.account_id.endpoint}/{"printjobs"}'

        resp = requests.post(
            post_url,
            auth=auth,
            json=data
        )

        if resp.status_code == 201:
            job_id = resp.json()

            printjob = self.env['printnode.printjob'].sudo().search([('id', '=', printjob_id)])
            printjob.sudo().write({'printnode_id': str(job_id)})
        else:
            if 'application/json' in resp.headers.get('Content-Type'):
                message = resp.json().get('message', _('Something went wrong. Try again later'))
            else:
                message = _(
                    'Looks like printing service is currently unavailable. '
                    'Please contact us: support@ventor.tech'
                )

            raise UserError(_('Cannot send printjob: {}').format(message))

        return job_id

    def _format_title(self, objects, copies):
        if len(objects) == 1:
            return f'{objects.display_name}_{copies}'
        return f'{objects._description}_{len(objects)}_{copies}'

    def _get_source_name(self):
        full_version = self.env['ir.module.module'].sudo().search(
            [['name', '=', 'printnode_base']]).latest_version

        split_value = full_version and full_version.split('.')
        module_version = split_value and '.'.join(split_value[-3:])
        source_name = f'Odoo Direct Print Lite {module_version}'

        return source_name

    def _get_data_options(self, params=None):
        """
        Prepare print data options
        """
        options = {}
        if params:
            options.update(params)

        return options

    def _get_content_type(self, report_type=None):
        """
        Get content type
        """
        return 'pdf_base64' if report_type in ['qweb-pdf', 'py3o'] else 'raw_base64'
