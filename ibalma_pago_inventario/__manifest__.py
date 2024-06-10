# -*- coding: utf-8 -*-

{
    'name': 'Odoo/Wecare',
    'version': '1.0',
    'summary': 'Modificación a Odoo para implementación de Pago de Inventario IMJ',
    'description': """
    Modificación a Odoo para implementación de Pago de Inventario IMJ 
    """,
    'website': 'https://www.itreingenierias.com',
    'data': [
        'views/pago_inventario.xml',
    ],
    'depends': [
                'sale_stock_margin',
                ],
    "license": 'LGPL-3',
}