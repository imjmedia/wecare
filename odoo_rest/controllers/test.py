# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
#################################################################################
from odoo.addons.web.controllers.main import Home
# import odoo_rest
# import xml
import json
import xml.etree.ElementTree as ET
import werkzeug
from odoo.http import request, Controller, route
import logging
_logger = logging.getLogger(__name__)
from functools import wraps
from ast import literal_eval

def _checkAllFieldType(modelObj ,filter_fields, model_id):

	IrModelFieldsObj = request.env["ir.model.fields"].sudo()

	# binary fields name list
	binaryFields =  IrModelFieldsObj.search_read([("model_id","=",model_id),("ttype","=","binary")],fields=['name'])
	binaryFieldsLst = [field.get('name') for field in binaryFields]
	if filter_fields:
		binaryFieldsLst = list(set(binaryFieldsLst).intersection(filter_fields))
	_logger.info("---------binaryFieldsLst----%r----",binaryFieldsLst)

	# O2M fields name list
	O2MFields =  IrModelFieldsObj.search_read([("model_id","=",model_id),("ttype","=","one2many")],fields=['name'])
	O2MFieldsLst = [field.get('name') for field in O2MFields]
	if filter_fields:
		O2MFieldsLst = list(set(O2MFieldsLst).intersection(filter_fields))
	_logger.info("--------O2MFieldsLst-----%r----",O2MFieldsLst)

	# M2M fields name list
	M2MFields =  IrModelFieldsObj.search_read([("model_id","=",model_id),("ttype","=","many2many")],fields=['name'])
	M2MFieldsLst = [field.get('name') for field in M2MFields]
	if filter_fields:
		M2MFieldsLst = list(set(M2MFieldsLst).intersection(filter_fields))
	_logger.info("------M2MFieldsLst-------%r----",M2MFieldsLst)

	# non relational and non binary fields except many2one
	field_type = ['boolean','char','date','datetime','float','html','integer','monetary','selection','text']
	NormalFields =  IrModelFieldsObj.search_read([("model_id","=",model_id),("ttype","in",field_type)],fields=['name'])
	NormalFieldsLst = [field.get('name') for field in NormalFields]
	if filter_fields:
		NormalFieldsLst = list(set(NormalFieldsLst).intersection(filter_fields))
	_logger.info("--------NormalFieldsLst-----%r----",NormalFieldsLst)






def _checkByteData(dic):
	modified_dic = {}
	for key, val in dic.items():
		if isinstance(val, bytes):
			modified_dic.update({key: val.decode('utf-8')})
		else:
			modified_dic.update({key: val})
	return modified_dic

def _checkbinaryFieldsData(model_id,fields,data):
	binaryFields =  request.env["ir.model.fields"].sudo().search_read([("model_id","=",model_id),
															("ttype","=","binary")],fields=['name'])
	binaryFieldsName = [field.get('name') for field in binaryFields]
	if fields:
		common_fields = list(set(binaryFieldsName).intersection(fields))
		if common_fields:
			for d in data:
				for common in common_fields:
					if isinstance(d[common], bytes):
						d[common] = d[common].decode('utf-8')
	else:
		for d in data:
			for binary in binaryFieldsName:
				if isinstance(d[binary], bytes):
					d[binary] = d[binary].decode('utf-8')
	return data

def _checkOne2ManyFieldsData(model_id,fields,data,modelObj):
	One2ManyFields =  request.env["ir.model.fields"].sudo().search_read([("model_id","=",model_id),
															("ttype","=","one2many")],fields=['name'])
	One2ManyFieldsName = [field.get('name') for field in One2ManyFields]
	if fields:
		common_fields = list(set(One2ManyFieldsName).intersection(fields))
		if common_fields:
			_logger.info("-------common_fields------%r----",common_fields)
			_logger.info("-------modelObj------%r----",modelObj)

			for d in data:
				for common in common_fields:
					if isinstance(d[common], bytes):
						d[common] = d[common].decode('utf-8')
	else:
		_logger.info("-------One2ManyFieldsName------%r----",One2ManyFieldsName)
		_logger.info("-------modelObj------%r----",modelObj)
		# for d in data:
		# 	for o2m in One2ManyFieldsName:
		# 		if isinstance(d[binary], bytes):
		# 			d[o2m] = d[o2m].decode('utf-8')
	# return data

class xml(object):

	@staticmethod
	def _encode_content(data):
		# .replace('&', '&amp;')
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

	def __decorateMe(func):
		@wraps(func)
		def wrapped(inst, **kwargs):
			inst._mData = request.httprequest.data and json.loads(request.httprequest.data.decode('utf-8')) or {}
			inst.ctype = request.httprequest.headers.get('Content-Type')== 'text/xml' and 'text/xml'  or 'json'
			return func(inst,**kwargs)
		return wrapped

	def _available_api(self):
		API = {
			'api':{
						'description':'HomePage API',
						'uri':'/mobikul/homepage'
					},
			'sliderProducts':{
						'description':'Product(s) of given Product Slider Record',
						'uri':'/mobikul/sliderProducts/&lt;int:product_slider_id&gt;',
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
		if 'confObj' in response.keys():
			response.pop('confObj')
		if ctype =='json':
			mime='application/json; charset=utf-8'
			body = json.dumps(response)
		else:
			mime='text/xml'
			body = self._wrap2xml(apiName,response)
		headers = [
					('Content-Type', mime),
					('Content-Length', len(body))
				]
		return werkzeug.wrappers.Response(body, headers=headers)

	@__decorateMe
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
	def getRecordData(self, object_name, record_id, **kwargs):
		response = self._authenticate(**kwargs)
		if response.get('success'):
			try:
				response.update(response['confObj']._check_permissions(object_name))
				if response.get('success') and response.get('permisssions').get('read'):
					modelObjData = request.env[object_name].sudo().search([('id','=',record_id)])
					data = request.env[object_name].sudo().search_read([('id','=',record_id)])
					if not data:
						response['message'] = "No Record found for id(%s) in given model(%s)."%(record_id, object_name)
						response['success'] = False
					else:
						_checkOne2ManyFieldsData(response.get('model_id'),[],data,modelObjData)
						data = _checkbinaryFieldsData(response.get('model_id'),[],data)
						response['data'] = data
				else:
					response['message'] = "You don't have read permission of the model '%s'" % object_name
					response['success'] = False
			except Exception as e:
				response['message'] = "ERROR: %r"%e
				response['success'] = False
		return self._response(object_name, response,self.ctype)

	@route(['/api/<string:object_name>/search'], type='http', auth="none", csrf=False, methods=['POST'])
	def getSearchData(self, object_name, **kwargs):
		response = self._authenticate(**kwargs)
		if response.get('success'):
			try:
				response.update(response['confObj']._check_permissions(object_name))
				if response.get('success') and response.get('permisssions').get('read'):
					domain = self._mData.get('domain') and literal_eval(self._mData.get('domain')) or []
					fields = self._mData.get('fields') and literal_eval(self._mData.get('fields')) or []
					offset = int(self._mData.get('offset', 0))
					limit = int(self._mData.get('limit', 0))
					order = self._mData.get('order', None)
					modelObjData = request.env[object_name].sudo().search(domain, offset=offset,
																	   limit=limit, order=order)
					data = request.env[object_name].sudo().search_read(domain=domain, fields=fields, offset=offset,
																	   limit=limit, order=order)

					if not data:
						response['message'] = "No Record found for given criteria in model(%s)." % (object_name)
						response['success'] = False
					else:
						_checkOne2ManyFieldsData(response.get('model_id'),fields,data,modelObjData)
						data = _checkbinaryFieldsData(response.get('model_id'),fields,data)
						response['data'] = data
				else:
					response['message'] = "You don't have read permission of the model '%s'" % object_name
					response['success'] = False
			except Exception as e:
				response['message'] = "ERROR: %r %r" % (e, kwargs)
				response['success'] = False
		return self._response(object_name, response, self.ctype)
