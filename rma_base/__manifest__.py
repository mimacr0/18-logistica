# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2026 DaFe Solutions
#
##############################################################################

{
    'name': "RMA Base",
    'category': 'All',
    'version': '18.0.1.0.0',
    'author': 'Dafe Solutions LLC',
    'maintainer': 'DaFe Solutions',
    'description': """Product Menu module""",
    'depends': ['base', 'account_partner', 'stock'],
    'license': 'LGPL-3',
    'website': "https://www.dafe.es",
    'data': [
        'security/ir.model.access.csv',
        'views/account_product_map_views.xml',
        'views/product_product_views.xml',
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # 'rma_base/static/src/backend/js/**.js',
            # 'rma_base/static/src/backend/xml/**.xml',
            # 'rma_base/static/src/backend/scss/**.scss',
        ],
        'web.assets_frontend': [
            # 'rma_base/static/src/frontend/js/**.js',
            # 'rma_base/static/src/frontend/xml/**.xml',
            # 'rma_base/static/src/frontend/scss/**.scss',
        ],
    },
    'images': ['/static/description/icon.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
