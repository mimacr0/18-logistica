# -*- coding: utf-8 -*-
{
    'name': "Stock Barcode Auto Serial",
    'category': 'Inventory',
    'version': '18.0.1.0.0',
    'author': 'DaFe Solutions',
    'maintainer': 'DaFe Solutions',
    'description': """
        Automatic serial number generation for barcode operations.
        Generates serial numbers for products with tracking='serial' that don't have a serial assigned.
    """,
    'summary': """Automatic Serial Number Generation for Barcode""",
    'depends': ['stock', 'stock_barcode'],
    'license': 'LGPL-3',
    'website': "https://www.dafe.es",
    'data': [
        'security/ir.model.access.csv',
        'wizards/generate_serial_wizard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'stock_barcode_auto_serial/static/src/models/barcode_picking_model.js',
        ]
    },
    'images': ['static/description/icon.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
