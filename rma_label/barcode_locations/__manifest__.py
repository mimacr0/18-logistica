# -*- coding: utf-8 -*-
{
    'name': "Barcode Locations",
    'category': 'Inventory',
    'version': '18.0.1.0.0',
    'author': 'Dafe Solutions LLC',
    'maintainer': 'Dafe Solutions LLC',
    'description': """Module to manage barcode locations""",
    'summary': """Barcode Locations Management""",
    'depends': ['stock'],
    'license': 'LGPL-3',
    'website': "https://www.dafe.es",
    'data': [
        'views/templates.xml',
        'views/stock_location_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'barcode_locations/static/src/js/list_controller.js',
            'barcode_locations/static/src/xml/list_view_buttons.xml',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
}
