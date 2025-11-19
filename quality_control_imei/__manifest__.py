# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2025 DaFe Solutions
#
##############################################################################

{
    'name': "Quality Control IMEI",
    'category': 'Inventory',
    'version': '18.0.1.0.0',
    'author': 'DaFe Solutions',
    'description': """Modulo para el control de calidad de IMEI con validacion via API""",
    'summary': """Quality Control IMEI with API Validation""",
    'depends': ['stock', 'quality_control'],
    'license': 'LGPL-3',
    'website': "https://www.dafe.es",
    'external_dependencies': {
        'python': ['requests'],
    },
    'data': [
        'security/ir.model.access.csv',
        'wizards/generate_serial_wizard_views.xml',
        'views/res_config_settings_views.xml',
        'views/quality_check_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
        ]
    },
    'images': ['static/description/icon.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
