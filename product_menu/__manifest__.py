# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2025 DaFe Solutions
#
##############################################################################

{
    'name': "Product Menu",
    'category': 'Settings',
    'version': '18.0.1.0.0',
    'author': 'DaFe Solutions',
    'maintainer': 'DaFe Solutions',
    'description': """Modulo para la gestión de clientes y cuentas en el portal""",
    'summary': """Menu productos""",
    'depends': ['stock', 'client_account'],
    'license': 'LGPL-3',
    'website': "https://www.dafe.es",
    'data': [
        'security/ir.model.access.csv',
        'data/product_attribute_data.xml',
        'data/product_category_data.xml',
        'wizard/account_add_products_wizard.xml',
        'wizard/product_images_import_wizard.xml',
        'views/product_template_views.xml',
        'views/product_template_attribute_line_views.xml',
        'views/product_template_value_views.xml',
        'views/product_product_views.xml',
        'views/product_category_views.xml',
        'views/menu_product.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'product_menu/static/src/**/*.xml',
            'product_menu/static/src/**/*.js',
        ]
    },
    'images': ['static/description/icon.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
    'post_init_hook': 'post_init_hook',
}