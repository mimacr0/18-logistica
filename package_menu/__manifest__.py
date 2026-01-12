# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2025 DaFe Solutions
#
##############################################################################

{
    'name': "Package Menu",
    'category': 'Settings',
    'version': '18.0.1.0.0',
    'author': 'DaFe Solutions',
    'maintainer': 'DaFe Solutions',
    'description': """Modulo para la gestión de clientes y cuentas en el portal""",
    'summary': """Menu paquetes""",
    'depends': ['stock', 'client_account', 'stock_delivery', 'logistics_security'],
    'license': 'LGPL-3',
    'website': "https://www.dafe.es",
    'data': [
        'data/stock_package_sequence.xml',
        'data/stock_package_type_data.xml',
        'views/stock_quant_package_views.xml',
        'views/menu.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'assets': {
        'web.assets_backend': [
 
        ]
    },
    'images': ['static/description/icon.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}