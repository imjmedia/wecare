# Copyright 2023 VentorTech OU
# See LICENSE file for full copyright and licensing details.

import base64
import json
import logging
import werkzeug

from odoo import http
from odoo.http import request, serialize_exception
from odoo.tools.translate import _

from odoo.addons.web.controllers.report import ReportController


_logger = logging.getLogger(__name__)

SECURITY_GROUP = 'printnode_base_lite.printnode_security_group_user'
SUPPORTED_REPORT_TYPES = [
    'qweb-pdf',
    'qweb-text',
    'py3o',
]


class ReportControllerProxy(ReportController):

    def _check_direct_print(self, data, context):
        """
        This method performs multi-step data validation before sending a print job.

        :param data: a list of params such as report_url, report_type, printer_id
        :param context: current context
        """
        print_data = {'can_print': False}
        request_content = json.loads(data)

        report_url, report_type, printer_id = \
            request_content[0], request_content[1], request_content[2]

        print_data['report_type'] = report_type

        if printer_id:
            printer_id = request.env['printnode.printer'].browse(printer_id)

        # STEP 1: First check if direct printing is enabled for user at all.
        # If no - not need to go further
        user = request.env.user
        if not user.has_group(SECURITY_GROUP) \
                or not request.env.company.printnode_enabled \
                or (not user.printnode_enabled and not printer_id):
            return print_data

        # STEP 2: If we are requesting not PDF or Text file, than also return
        # to standard Odoo behavior.
        if report_type not in SUPPORTED_REPORT_TYPES:
            return print_data

        extension = report_type
        if '-' in report_type:
            extension = report_type.split('-')[1]
        report_name = report_url.split(f'/report/{extension}/')[1].split('?')[0]

        if '/' in report_name:
            report_name, ids = report_name.split('/')

            if ids:
                ids = [int(x) for x in ids.split(",") if x.isdigit()]
                print_data['ids'] = ids

        report = request.env['ir.actions.report']._get_report_from_name(report_name)
        model = request.env[report.model_id.model]

        print_data['model'] = model

        # STEP 4. Now let's check if we can define printer for the current report.
        # If not - just reset to default
        if not printer_id:
            printer_id = user.get_report_printer(report.id)

        if not printer_id:
            return print_data

        print_data["printer_id"] = printer_id
        print_data["can_print"] = True

        return print_data

    @http.route('/report/check', type='http', auth="user")
    def report_check(self, data, context=None):
        print_data = self._check_direct_print(data, context)
        if print_data['can_print']:
            return "true"
        return "false"

    @http.route('/report/print', type='http', auth="user")
    def report_print(self, data, context=None):
        """
        Handles sending a report to a printer.

        :param data: The data to be printed.
        :param context optional: dict with current context.
        :return: a JSON-encoded response with info about the success or failure of the print job.
        """
        print_data = self._check_direct_print(data, context)
        if not print_data['can_print']:
            return json.dumps({
                'title': _('Printing not allowed!'),
                'message': _('Please check your DirectPrint settings or close and open app again'),
                'success': False,
                'notify': True,
            })

        printer_id = print_data['printer_id']

        # Finally if we reached this place - we can send report to printer.
        standard_response = self.report_download(data, context)

        # If we do not have Content-Disposition headed, than no file-name
        # was generated (maybe error)
        content_disposition = standard_response.headers.get('Content-Disposition')
        if not content_disposition:
            return standard_response

        report_name = content_disposition.split("attachment; filename*=UTF-8''")[1]
        report_name = werkzeug.urls.url_unquote(report_name)
        ascii_data = base64.b64encode(standard_response.data).decode('ascii')

        try:
            params = {
                'title': report_name,
                'type': print_data['report_type'],
                'options': {},
            }
            printer_id.printnode_print_b64(ascii_data, params)
        except Exception as exc:
            _logger.exception(exc)
            error = {
                'success': False,
                'code': 200,
                'message': "Odoo Server Error",
                'data': serialize_exception(exc)
            }
            return json.dumps(error)

        title = _('Report was sent to printer')
        message = _(
            'Document "%(report)s" was sent to printer %(printer)s',
            report=report_name,
            printer=printer_id.name,
        )
        return json.dumps({
            'title': title,
            'message': message,
            'success': True,
            'notify': request.env.company.im_a_teapot
        })


class DPCCallbackController(http.Controller):
    @http.route('/dpc-lite-callback', type='http', auth='user')
    def dpc_callback(self, **kwargs):
        """
        Callback method to update main account with current api_key.

        When the user following the link in the wizard gets to "print.ventor.tech" and registers
        there, he gets an API key, after that he will be redirected back to Oduu to this controller.
        This method will first update the API key for the current account, and then redirect the
        user to the settings page.
        """
        if 'api_key' not in kwargs:
            return _('No API Key returned. Please, copy the key and paste in the module settings')

        request.env['printnode.account'].update_main_account(kwargs['api_key'])

        settings_action_id = request.env.ref('printnode_base_lite.printnode_settings_action').id
        return werkzeug.utils.redirect(
            f'/web?view_type=form&model=res.config.settings#action={settings_action_id}'
        )
