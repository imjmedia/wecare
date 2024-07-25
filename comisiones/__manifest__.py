# -*- coding: utf-8 -*-
{
    'name': "Comisiones Ibalma",

    'summary': """
        Modulo para generar comisiones de Ibalma.""",

    'author': "IT Reingenierias S de RL",
    'website': "http://www.itreingenierias.com",
    'version': '17.0.1',
    'data': [
        'security/ir.model.access.csv',
        'report/comisiones.xml',
        'views/comision.xml',
    ],
    'depends': [
        'sale',
        'account',
        'base',
        'product',
    ],
    "license": 'LGPL-3',
}