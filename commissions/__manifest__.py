# coding: utf-8
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Sale Commissions',
    'version': '15.0.1.0.0',
    'summary': 'Sales commissions for commercials WeCare',
    'description': """Sales commissions for commercials WeCare.""",
    'license': 'AGPL-3',
    'author': "Morfosys / ToDOO Web",
    'category': 'Sale',
    'website': "https://morfosys.com.mx/",
    'support': 'soporte@morfosys.com.mx',    
    'depends': ['base', 'sale', 'sale_management'],
    'data': [
        'security/commission_security.xml',
        'security/ir.model.access.csv',
        'views/sale_commission_view.xml',
        'views/res_user_view.xml',
        'data/ir_sequence.xml',
        'data/ir_config_parameter.xml',
        'views/sale_order_view.xml',
    ],
    'images': [
       'static/description/screenshot_commision.png'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 15,
    'currency': 'USD',
}
