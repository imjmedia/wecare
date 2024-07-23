# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Akhil Ashok (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Direct Print',
    'version': '15.0.1.0.0',
    'summary': 'The Direct Print is a tool that connects Odoo to PrintNode, '
               'a cloud-based printing service. This connector allows users to'
               ' send print jobs from their Odoo environment to any printer '
               'connected to their PrintNode account.',
    'description': 'PrintNode is a cloud-based printing service that enables '
                   'businesses to print documents remotely from any device or '
                   'location. The Direct Print for Odoo is a '
                   'software module that integrates Odoo, an open-source ERP '
                   'system, with PrintNodes printing capabilities.',
    'category': 'Extra tools',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    "external_dependencies": {
        'python': ['printnodeapi']
    },
    'license': 'LGPL-3',
    'depends': ['base', 'base_setup'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/printer_details_views.xml',
    ],
    'images': [
        'static/description/banner.jpg',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
