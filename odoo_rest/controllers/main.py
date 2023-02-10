# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
#################################################################################
import json
import xml.etree.ElementTree as ET
import werkzeug
from odoo.http import request, Controller, route
import logging
_logger = logging.getLogger(__name__)
from functools import wraps
from ast import literal_eval
from odoo.models import BaseModel
from odoo.service.model import execute_kw
from datetime import date, datetime, time
from odoo import api, fields, models, _, SUPERUSER_ID
import xmlrpc.client


NON_RELATIONAL_FIELDS = ['boolean','char','float','html','integer','monetary','text','selection',
# 'date','datetime'
]

def _fetch_coloumn_names (Modelobj,filter_field):
	ModelFields = {}
	if filter_field:
		for ff in filter_field:
			ModelFields.update({ff:[Modelobj._fields.get(ff),Modelobj._fields.get(ff).type,Modelobj._fields.get(ff).store]})
	else:
		for model_key, model_value in Modelobj._fields.items():
			ModelFields.update({model_key:[model_value,model_value.type,model_value.store]})
	return ModelFields

def  _fetchAllFieldData(obj,filter_field):
	if filter_field and (not 'id' in filter_field):
		filter_field.append('id')

	all_coloumns = _fetch_coloumn_names(obj,filter_field)
	record = _fetchColoumnData(obj,all_coloumns)
	return record

def _fetchColoumnData(obj,all_coloumns):
	record = {}
	for field_name, arr in all_coloumns.items():
		# execute if store = true eg. {arr[2] = store}

		if arr[2]:

			if arr[1] in NON_RELATIONAL_FIELDS:
				record.update({field_name:getattr(obj, field_name)})
			elif arr[1] == 'one2many':
				if getattr(obj, field_name):
					arr = []
					for o in getattr(obj, field_name):
						temp = {"id":o.id,}
						if hasattr(o, "name") and isinstance(o.name, str):
							temp.update({"name": o.name })
						arr.append(temp)
					record.update({field_name:arr})
			elif arr[1] == 'many2one':
				try:
					record.update({field_name: getattr(obj, field_name).read(['id','name'])})
				except Exception as e:
					record.update({field_name: getattr(obj, field_name).read(['id'])})

			elif arr[1] == 'binary':
				record.update({field_name: getattr(obj, field_name) and getattr(obj, field_name).decode('utf-8') or False})
			elif arr[1] == 'date':
				record.update({field_name: getattr(obj, field_name) and getattr(obj, field_name).isoformat() or False})
			elif arr[1] == 'datetime':
				record.update({field_name: getattr(obj, field_name) and getattr(obj, field_name).isoformat() or False})
			elif arr[1] == 'many2many':
				pass
			else:
				_logger.info("WARNING : %s FIELD IS ABSENT IN THE MODEL"%field_name)


	return record

def _fetchModelData(modelObj ,filter_field,model_id):
	data = []
	for obj in modelObj:

		data.append( _fetchAllFieldData(obj,filter_field))
	return data

def _updateModelData(Modelobj,data,model_id):
	return Modelobj.write(data)

def _deleteModelData(Modelobj,model_id):
	return Modelobj.unlink()

def _createModelData(Modelobj,data,model_id):
	return Modelobj.create(data).id


def _fetchModelSchema(Modelobj,model_id):
	data = []
	for field_key, field_value in Modelobj._fields.items():
		result={"field_name":field_key,"field_type": field_value.type,"label":field_value.string,"required":field_value.required,"readonly":field_value.readonly}
		if field_value.type == 'selection':
			result.update({"selection":field_key in ['lang','tz'] and " " or field_value.selection})
		data.append(result)

		# if field_value.type == "many2one":
		# 	data.append({model_key:field_value.type})
		# 	_logger.info("--selection----%r----",dir(field_value))
		# 	for method in dir(field_value):
		# 		_logger.info("--method--%r---return-%r----", method,getattr(model_value,method))
		# 	break
	return data



class xml(object):

	@staticmethod
	def _encode_content(data):
		return data.replace('<','&lt;').replace('>','&gt;').replace('"', '&quot;').replace('&', '&amp;')

	@classmethod
	def dumps(cls, apiName, obj):
		_logger.warning("%r : %r"%(apiName, obj))
		if isinstance(obj, dict):
			return "".join("<%s>%s</%s>" % (key, cls.dumps(apiName, obj[key]), key) for key in obj)
		elif isinstance(obj, list):
			return "".join("<%s>%s</%s>" % ("L%s" % (index+1), cls.dumps(apiName, element),"L%s" % (index+1)) for index,element in enumerate(obj))
		else:
			return "%s" % (xml._encode_content(obj.__str__()))

	@staticmethod
	def loads(string):
		def _node_to_dict(node):
			if node.text:
				return node.text
			else:
				return {child.tag: _node_to_dict(child) for child in node}
		root = ET.fromstring(string)
		return {root.tag: _node_to_dict(root)}


class RestWebServices(Controller):

	def __authenticate(func):
		@wraps(func)
		def wrapped(inst, **kwargs):
			inst._mData = request.httprequest.data and json.loads(request.httprequest.data.decode('utf-8')) or {}
			inst.ctype = request.httprequest.headers.get('Content-Type') == 'text/xml' and 'text/xml' or 'json'
			inst._auth = inst._authenticate(**kwargs)
			return func(inst, **kwargs)
		return wrapped

	# def __decorateMe(func):
	# 	@wraps(func)
	# 	def wrapped(inst, **kwargs):
	# 		inst._mData = request.httprequest.data and json.loads(request.httprequest.data.decode('utf-8')) or {}
	# 		inst.ctype = request.httprequest.headers.get('Content-Type') == 'text/xml' and 'text/xml'  or 'json'
	# 		return func(inst,**kwargs)
	# 	return wrapped

	def _available_api(self):
		API = {
			'api':{
						'description':'HomePage API',
						'uri':'/mobikul/homepage'
					},
		}
		return API

	def _wrap2xml(self, apiName, data):
		resp_xml = "<?xml version='1.0' encoding='UTF-8'?>"
		resp_xml += '<odoo xmlns:xlink="http://www.w3.org/1999/xlink">'
		resp_xml += "<%s>"%apiName
		resp_xml += xml.dumps(apiName, data)
		resp_xml += xml.dumps(apiName, data)
		resp_xml += "</%s>"%apiName
		resp_xml += '</odoo>'
		return resp_xml

	def _response(self, apiName, response, ctype='json'):
		body = {}

		if 'confObj' in response.keys():
			response.pop('confObj')
		if ctype =='json':
			mime='application/json; charset=utf-8'

			try:
				body = json.dumps(response,default=lambda o: o.__dict__)
			except Exception as e:
				body['message'] = "ERROR: %r" % (e)
				body['success'] = False
				body = json.dumps(body,default=lambda o: o.__dict__)

		else:
			mime='text/xml'
			body = self._wrap2xml(apiName,response)
		headers = [
					('Content-Type', mime),
					('Content-Length', len(body))
				]
		return werkzeug.wrappers.Response(body, headers=headers)

	# @__decorateMe
	def _authenticate(self, **kwargs):
		if 'api_key' in kwargs.keys():
			api_key  = kwargs.get('api_key')
		elif request.httprequest.authorization:
			api_key  = request.httprequest.authorization.get('password') or request.httprequest.authorization.get("username")
		elif request.httprequest.headers.get('api_key'):
			api_key = request.httprequest.headers.get('api_key') or None
		else:
			api_key = False
		RestAPI = request.env['rest.api'].sudo()
		response = RestAPI._validate(api_key)
		response.update(kwargs)
		return response

	@route('/api/', csrf=False, type='http', auth="none")
	def index(self, **kwargs):
		""" HTTP METHOD : request.httprequest.method
		"""
		response = self._authenticate(**kwargs)
		if response.get('success'):
			data = self._available_api()
			return self._response('api', data,'text/xml')
		else:
			headers=[('WWW-Authenticate','Basic realm="Welcome to Odoo Webservice, please enter the authentication key as the login. No password required."')]
			return werkzeug.wrappers.Response('401 Unauthorized %r'%request.httprequest.authorization, status=401, headers=headers)


	@route(['/api/<string:object_name>/<int:record_id>'], type='http', auth="none",methods=['GET'], csrf=False)
	@__authenticate
	def getRecordData(self, object_name, record_id, **kwargs):
		response = self._auth
		if response.get('success'):
			try:
			# if True:
				response.update(response['confObj']._check_permissions(object_name))
				if response.get('success') and response.get('permisssions').get('read'):
					fields = request.httprequest.values.get('fields') and literal_eval(request.httprequest.values.get('fields')) or []
					modelObjData = request.env[object_name].sudo().search([('id','=',record_id)])

					if not modelObjData:
						response['message'] = "No Record found for id(%s) in given model(%s)."%(record_id, object_name)
						response['success'] = False
					else:
						data = _fetchModelData(modelObjData,fields,response.get('model_id'))
						response['data'] = data
				else:
					response['message'] = "You don't have read permission of the model '%s'" % object_name
					response['success'] = False
			except Exception as e:
				response['message'] = "ERROR: %r"%e
				response['success'] = False
		return self._response(object_name, response,self.ctype)


	@route(['/api/<string:object_name>/search'], type='http', auth="none", csrf=False, methods=['GET'])
	@__authenticate
	def getSearchData(self, object_name, **kwargs):
		response = self._auth
		if response.get('success'):
			try:
				response.update(response['confObj']._check_permissions(object_name))
				if response.get('success') and response.get('permisssions').get('read'):
					domain = request.httprequest.values.get('domain') and literal_eval(request.httprequest.values.get('domain')) or []
					fields = request.httprequest.values.get('fields') and literal_eval(request.httprequest.values.get('fields')) or []
					offset = int(request.httprequest.values.get('offset', 0))
					limit = int(request.httprequest.values.get('limit', 0))
					order = request.httprequest.values.get('order', None)

					modelObjData = request.env[object_name].sudo().search(domain, offset=offset,
																	   limit=limit, order=order)
					if not modelObjData:
						response['message'] = "No Record found for given criteria in model(%s)." % (object_name)
						response['success'] = False
					else:
						data = _fetchModelData(modelObjData,fields,response.get('model_id'))
						response['data'] = data
				else:
					response['message'] = "You don't have read permission of the model '%s'" % object_name
					response['success'] = False
			except Exception as e:
				# pass
				response['message'] = "ERROR: %r %r" % (e, kwargs)
				response['success'] = False
		return self._response(object_name, response, self.ctype)

	@route(['/api/<string:object_name>/<int:record_id>'], type='http', auth="none", methods=['PUT'], csrf=False)
	@__authenticate
	def updateRecordData(self, object_name, record_id, **kwargs):
		response = self._auth
		if response.get('success'):
			try:
				response.update(response['confObj']._check_permissions(object_name))
				if response.get('success') and response.get('permisssions').get('write'):
					data = self._mData
					modelObjData = request.env[object_name].sudo().search([('id', '=', record_id)])
					if not modelObjData:
						response['message'] = "No Record found for id(%s) in given model(%s)." % (
						record_id, object_name)
						response['success'] = False
					else:
						_updateModelData(modelObjData, data, response.get('model_id'))
						response['success'] = True
				else:
					response['message'] = "You don't have write permission of the model '%s'" % object_name
					response['success'] = False
			except Exception as e:
				response['message'] = "ERROR: %r" % e
				response['success'] = False
		return self._response(object_name, response, self.ctype)



	@route(['/api/<string:object_name>/<int:record_id>'], type='http', auth="none", methods=['DELETE'], csrf=False)
	@__authenticate
	def deleteRecordData(self, object_name, record_id, **kwargs):
		response = self._auth
		if response.get('success'):
			try:
				response.update(response['confObj']._check_permissions(object_name))
				if response.get('success') and response.get('permisssions').get('delete'):
					modelObjData = request.env[object_name].sudo().search([('id', '=', record_id)])
					if not modelObjData:
						response['message'] = "No Record found for id(%s) in given model(%s)." % (record_id, object_name)
						response['success'] = False
					else:
						_deleteModelData(modelObjData,response.get('model_id'))
						response['success'] = True
				else:
					response['message'] = "You don't have delete permission of the model '%s'" % object_name
					response['success'] = False
			except Exception as e:
				response['message'] = "ERROR: %r" % e
				response['success'] = False
		return self._response(object_name, response, self.ctype)

	@route(['/api/<string:object_name>/create'], type='http', auth="public", csrf=False, methods=['POST'])
	@__authenticate
	def createSearchData(self, object_name, **kwargs):
		response = self._auth
		if response.get('success'):
			try:
				response.update(response['confObj']._check_permissions(object_name))
				if response.get('success') and response.get('permisssions').get('create'):
					data = self._mData
					modelObjData = request.env[object_name].sudo()
					id = _createModelData(modelObjData, data, response.get('model_id'))
					response['create_id'] = id
				else:
					response['message'] = "You don't have create permission of the model '%s'" % object_name
					response['success'] = False
			except Exception as e:
				response['message'] = "ERROR: %r %r" % (e, kwargs)
				response['success'] = False
		return self._response(object_name, response, self.ctype)

	@route(['/api/<string:object_name>/schema'], type='http', auth="none", csrf=False, methods=['GET'])
	@__authenticate
	def getSchema(self, object_name, **kwargs):
		response = self._auth
		if response.get('success'):
			try:
				response.update(response['confObj']._check_permissions(object_name))
				if response.get('success') and response.get('permisssions').get('read'):
					modelObj = request.env[object_name].sudo()
					data = _fetchModelSchema(modelObj, response.get('model_id'))
					response['data'] = data
				else:
					response['message'] = "You don't have read permission of the model '%s'" % object_name
					response['success'] = False
			except Exception as e:
				response['message'] = "ERROR: %r %r" % (e, kwargs)
				response['success'] = False
		return self._response(object_name, response, self.ctype)


	@route(['/api/<string:object_name>/execute_kw'], type='http', auth="none", csrf=False, methods=['POST'])
	@__authenticate
	def callMethod(self,object_name, **kwargs):
		response = self._auth
		response.update(response['confObj']._check_permissions(object_name))
		if response.get('success') and response.get('permisssions').get('read') and response.get('permisssions').get('create') and response.get('permisssions').get('delete') and response.get('permisssions').get('write') :
			db = request.httprequest.session.get('db')
			try:
				uid = 1
				request.context = dict(request.context,odoo_rest_api=True)
				result = execute_kw(db, uid, object_name, self._mData.get("method"), self._mData.get("args"),self._mData.get("kw",{}))
				if result:
					response['message'] = "Method Successfully Called"
					response['result'] = result
			except Exception as e:
				response['message'] = "ERROR: %r" % (e)
				response['success'] = False
		else:
			response['message'] = "You don't have appropriate permission of the model '%s'" % object_name
			response['success'] = False

		return self._response(object_name, response, self.ctype)
