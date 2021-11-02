# -*- coding: utf-8 -*-
{
    'name': "Habilitar Envío de Mercancía hasta que se genere el pago de la Orden de Venta",

    'summary': """
        Modulo para realizar gestión de envío de mercancía hasta que se realice el pago dentro de la factura.""",

    'author': "IT Reingenierias S de RL",
    'website': "http://www.itreingenierias.com",
    'version': '0.1',
    'data': [
        'views/pago_envio.xml',
    ],
    'depends': [
        'sale_stock',
    ],
}