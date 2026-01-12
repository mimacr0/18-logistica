# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2025 DaFe Solutions
#
##############################################################################

{
    'name': 'Stock Internal Transfers',
    'version': '18.0.1.0.0',
    'author': 'DaFe Solutions',
    'maintainer': 'DaFe Solutions',
    'description': """Módulo para personalizar las operaciones de traslado interno""",
    'summary': """Traslados internos personalizados""",
    'category': 'Inventory/Inventory',
    'depends': ['stock', 'hr'],
    'license': 'LGPL-3',
    'website': "https://www.dafe.es",
    'data': [
        'views/stock_picking_type_views.xml',
        'views/stock_picking_views.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
