# from odoo import http
# import logging
# from odoo.http import request
# _logger = logging.getLogger(__name__)

# def setup_db(self, httprequest):
#     db = httprequest.session.db
#     # Check if session.db is legit
#     if db:
#         if db not in http.db_filter([db], httprequest=httprequest):
#             _logger.warn("Logged into database '%s', but dbfilter "
#                          "rejects it; logging session out.", db)
#             httprequest.session.logout()
#             db = None

#     if not db:
#         if httprequest.headers.get('db_name'):
#             httprequest.session.db = httprequest.headers.get('db_name')
#         elif httprequest.values.get("db_name"):
#             httprequest.session.db = httprequest.values.get("db_name")
#         else:
#             httprequest.session.db = http.db_monodb(httprequest)

# http.root.setup_db = setup_db


from odoo import http
from odoo.http import route, request

class MyController(http.Controller):

    @route('/web/database/manager', type='http', auth="none")
    def web_database_manager(self, s_action=None, **kw):
        db_name = request.env.cr.dbname

        # Check if db_name is legit
        if db_name:
            if db_name not in http.db_filter([db_name]):
                _logger.warning("Logged into database '%s', but dbfilter "
                                "rejects it; logging session out.", db_name)
                request.session.logout()

        # Your custom logic here
        pass

