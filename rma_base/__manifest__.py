# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2026 DaFe Solutions
#
##############################################################################

{
    'name': "RMA Base",
    'category': 'All',
    'version': '18.0.1.17.0',
    'author': 'Dafe Solutions LLC',
    'maintainer': 'DaFe Solutions',
    'description': """Product Menu module""",
    'depends': ['base', 'web', 'mail', 'account_partner', 'product', 'stock'],
    'license': 'LGPL-3',
    'website': "https://www.dafe.es",
    'data': [
        'security/ir.model.access.csv',
        'wizards/account_add_products_wizard_views.xml',
        'wizards/account_product_map_import_wizard_views.xml',
        'wizards/pricelist_item_dates_wizard_views.xml',
        'views/account_product_map_views.xml',
        'views/product_product_views.xml',
        'views/product_template_views.xml',
        'views/res_partner_views.xml',
        'views/product_pricelist_views.xml',
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'rma_base/static/src/js/account_product_map_list_view.js',
            'rma_base/static/src/xml/account_product_map_list_buttons.xml',
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
