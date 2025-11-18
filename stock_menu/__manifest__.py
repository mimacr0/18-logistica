# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2025 DaFe Solutions
#
##############################################################################

{
    'name': "Stock Menu",
    'category': 'Settings',
    'version': '18.0.1.0.0',
    'author': 'DaFe Solutions',
    'description': """Modulo para la gestion de stock""",
    'summary': """Menu Stock""",
    'depends': ['stock', 'client_account'],
    'license': 'LGPL-3',
    'website': "https://www.dafe.es",
    'data': [
        'views/product_product.xml',
        'views/menu_product.xml',
    ],
    'assets': {
        'web.assets_backend': [
        ]
    },
    'images': ['static/description/logo.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}