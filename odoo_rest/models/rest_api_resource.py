# -*- coding: utf-8 -*-
##########################################################################
#
#    Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
##########################################################################
from odoo import api, fields, models, _, SUPERUSER_ID

class RestAPIResources(models.Model):
	_name = 'rest.api.resources'
	_description = 'REST API Resources'
	_rec_name = "model_id"

	model_id = fields.Many2one('ir.model', string='Resource',ondelete='set default', required=True)
	api_id = fields.Many2one('rest.api', string='Corressponding API')
	read_ok = fields.Boolean("Read (GET)", default=True)
	write_ok = fields.Boolean("Write (PUT)", default=True)
	create_ok = fields.Boolean("Create (POST)", default=True)
	unlink_ok = fields.Boolean("Unlink (DELETE)", default=True)
