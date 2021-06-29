# Part of Odoo. See LICENSE file for full copyright and licensing details.

from os import path

from lxml import objectify
from odoo.tools import misc
from odoo.tests.common import Form

from odoo.addons.l10n_mx_edi.tests.common import TestMxEdiCommon


class TestMxEdiFactoring(TestMxEdiCommon):

    def test_factoring(self):
        self.certificate._check_credentials()
        invoice = self.invoice
        invoice.company_id.sudo().name = 'YourCompany Factoring'
        invoice.action_post()
        generated_files = self._process_documents_web_services(self.invoice, {'cfdi_3_3'})
        self.assertTrue(generated_files)
        self.assertEqual(invoice.edi_state, "sent", invoice.message_ids.mapped('body'))
        factoring = invoice.partner_id.sudo().create({
            'name': 'Financial Factoring',
            'country_id': self.env.ref('base.mx').id,
            'type': 'invoice',
        })
        invoice.partner_id.sudo().commercial_partner_id.l10n_mx_edi_factoring_id = factoring
        invoice.l10n_mx_edi_factoring_id = factoring
        # Register the payment
        ctx = {'active_model': 'account.move', 'active_ids': invoice.ids, 'force_ref': True}
        bank_journal = self.env['account.journal'].search([('type', '=', 'bank'),
                                                           ('company_id', '=', invoice.company_id.id)], limit=1)
        payment = Form(self.env['account.payment.register'].with_context(ctx))
        payment.payment_date = invoice.date
        payment.l10n_mx_edi_payment_method_id = self.env.ref('l10n_mx_edi.payment_method_efectivo')
        payment.payment_method_id = self.env.ref('account.account_payment_method_manual_in')
        payment.journal_id = bank_journal
        payment.amount = invoice.amount_total
        payment.save().action_create_payments()
        payment = invoice._get_reconciled_payments()

        self.assertTrue(invoice.l10n_mx_edi_factoring_id, 'Financial Factor not assigned')
        payment.action_l10n_mx_edi_force_generate_cfdi()
        generated_files = self._process_documents_web_services(payment, {'cfdi_3_3'})
        xml_expected_str = misc.file_open(path.join(
            'l10n_mx_edi_factoring', 'tests', 'expected_payment.xml')).read().encode('UTF-8')
        xml_expected = objectify.fromstring(xml_expected_str)
        self.assertTrue(generated_files)
        xml = objectify.fromstring(generated_files[0])
        xml_expected.attrib['Folio'] = xml.attrib['Folio']
        xml_expected.attrib['Fecha'] = xml.attrib['Fecha']
        xml_expected.attrib['Sello'] = xml.attrib['Sello']
        xml_expected.attrib['Serie'] = xml.attrib['Serie']
        xml_expected.Complemento = xml.Complemento
        self.assertEqualXML(xml, xml_expected)

    def xml2dict(self, xml):
        """Receive 1 lxml etree object and return a dict string.
        This method allow us have a precise diff output"""
        def recursive_dict(element):
            return (element.tag,
                    dict((recursive_dict(e) for e in element.getchildren()),
                         ____text=(element.text or '').strip(), **element.attrib))
        return dict([recursive_dict(xml)])

    def assertEqualXML(self, xml_real, xml_expected):  # pylint: disable=invalid-name
        """Receive 2 objectify objects and show a diff assert if exists."""
        xml_expected = self.xml2dict(xml_expected)
        xml_real = self.xml2dict(xml_real)
        # "self.maxDiff = None" is used to get a full diff from assertEqual method
        # This allow us get a precise and large log message of where is failing
        # expected xml vs real xml More info:
        # https://docs.python.org/2/library/unittest.html#unittest.TestCase.maxDiff
        self.maxDiff = None
        self.assertEqual(xml_real, xml_expected)
