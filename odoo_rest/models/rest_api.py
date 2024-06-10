# -*- coding: utf-8 -*-
##########################################################################
#
#    Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
##########################################################################
from odoo import models, fields,_, api
from odoo.exceptions import UserError
import random
import string
import datetime
import logging
_logger = logging.getLogger(__name__)


def _default_unique_key(size, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for x in range(size))


class RestAPI(models.Model):
	_name = "rest.api"
	_description = "RESTful Web Services"

	def _default_unique_key(size, chars=string.ascii_uppercase + string.digits ):
		return ''.join(random.choice(chars) for x in range(size))

	@api.model
	def _check_permissions(self, model_name, context=None):
		response = {'success':True, 'message':'OK','permisssions':{}}
		model_exists = self.env['ir.model'].sudo().search([('model','=',model_name)])
		if not model_exists:
			response['success'] = False
			response['message'] = "Model(%s) doen`t exists !!!"%model_name
		elif self.availabilty == "all":
			response['success']= True
			response['message']= "Allowed all Models Permission: %s"%self.availabilty
			response['model_id'] = model_exists.id
			response['permisssions'].update({'read':True,'write':True,'delete':True,'create':True})
		else:
			#Check for existense
			resource_allowed = self.env['rest.api.resources'].sudo().search([('api_id','=',self.id),('model_id','=',model_exists.id)])
			if resource_allowed:
				response['success'] = True
				response['message'] = "Allowed %s Models Permission: %s" % (model_exists.name, self.availabilty)
				response['model_id'] = model_exists.id
				response['permisssions'].update({'read': resource_allowed.read_ok, 'write': resource_allowed.write_ok, 'delete': resource_allowed.unlink_ok, 'create': resource_allowed.create_ok})
			else:
				response['success'] = False
				response['message'] = "Sorry,you don`t have enough permission to access this Model(%s). Please consult with your Administrator."%model_name
		return response

	@api.model
	def _validate(self, api_key, context=None):
		context = context or {}
		response = {'success':False, 'message':'Unknown Error !!!'}
		if not api_key:
			response['responseCode'] = 0
			response['message'] = 'Invalid/Missing Api Key !!!'
			return response
		try:
			# Get Conf
			Obj_exists = self.sudo().search([('api_key','=',api_key)])
			if not Obj_exists:
				response['responseCode'] = 1
				response['message'] = "API Key is invalid !!!"
			else:
				response['success'] = True
				response['responseCode'] = 2
				response['message'] = 'Login successfully.'
				response['confObj'] = Obj_exists
		except Exception as e:
			response['responseCode'] = 3
			response['message'] = "Login Failed: %r"%e.message or e.name
		return response

	name = fields.Char('Name', required=1)
	description = fields.Text('Extra Information', help="Quick description of the key", translate=True)
	# api_key = fields.Char(string='API Secret key', default=_default_unique_key(32), required=1)
	api_key = fields.Char(string='API Secret key')
	active = fields.Boolean(default=True)
	resource_ids = fields.One2many('rest.api.resources','api_id', string='Choose Resources')
	availabilty = fields.Selection([
        ('all', 'All Resources'),
        ('specific', 'Specific Resources')], 'Available for', default='all',
        help="Choose resources to be available for this key.", required=1)

	def generate_secret_key(self):
		self.api_key = _default_unique_key(32)

	# @api.one
	def copy(self, default=None):
		raise UserError(_("You can't duplicate this Configuration."))

	# @api.multi
	def unlink(self):
		raise UserError(_('You cannot delete this Configuration, but you can disable/In-active it.'))
