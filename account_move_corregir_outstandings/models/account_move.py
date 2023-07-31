# -*- coding: utf-8 -*-

from odoo import fields, models, api, SUPERUSER_ID, _
import logging

_logger = logging.getLogger(__name__)

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'


    def regenerar_polizas_outstanding(self):
        '''Se llamará desde un cron
        '''
        cuentas_outstanding = self.env['account.account'].search([('name', 'ilike', '%outstanding%')])
        cuentas_ids = cuentas_outstanding.ids
        apuntes = self.search([('account_id', 'in', cuentas_ids), ('parent_state', '!=', 'cancel')])
        _logger.info("Cuentas a corregir: %s"%len(apuntes))
        i = 1
        for move in apuntes:
            cuenta_ok_id = move.journal_id.default_account_id.id
            query = "UPDATE account_move_line SET account_id = %s WHERE id=%s" % (cuenta_ok_id, move.id)
            self._cr.execute(query)
            if i % 100 == 0:
                _logger.info("Proceso: %s de %s"%(i, len(apuntes)))
            i+=1
        _logger.info("Proceso terminó exitosamente")


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_mail_template(self):
        """
        :return: the correct mail template baseda en grupo
        """
        usuario = self.env.user
        if usuario.has_group('account_move_corregir_outstandings.group_usar_plantilla_sw'):
            plantilla_sw = self.env['mail.template'].search([('name', '=', 'Factura SW')])
            if plantilla_sw:
                #return '__export__.mail_template_77_9d708080' #produccion
                return '__export__.mail_template_77_c2ae9992' #stag
        else:
            return super(AccountMove, self)._get_mail_template()