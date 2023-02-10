
from odoo.models import BaseModel
from odoo import api
from odoo.http import request
from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)

class BaseModel(models.AbstractModel):
    _inherit = 'base'

    def _read_format(self, fnames, load='_classic_read'):

        if request.context.get("odoo_rest_api"):
            data = [(record, {'id': record._ids[0]}) for record in self]
            use_name_get = (load == '_classic_read')
            for name in fnames:
                convert = self._fields[name].convert_to_read
                for record, vals in data:
                    # missing records have their vals empty
                    if not vals:
                        continue
                    try:
                        vals[name] = convert(record[name], record, use_name_get)
                        if record._fields.get(name).type == "datetime":
                            vals[name] = fields.Datetime.to_string(vals[name])
                        elif record._fields.get(name).type == "date":
                            vals[name] = fields.Date.to_string(vals[name])
                    except MissingError:
                        vals.clear()
            result = [vals for record, vals in data if vals]

            return result

        else:
            result = super(BaseModel,self)._read_format(fnames=fnames,load=load)
            return result
