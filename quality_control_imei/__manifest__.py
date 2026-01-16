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
    'maintainer': 'DaFe Solutions',
    'description': """IMEI validation via API for quality control. Requires manual IMEI entry for configured product categories.""",
    'summary': """Quality Control IMEI with API Validation""",
    'depends': ['stock', 'quality_control', 'stock_barcode_auto_serial'],
    'license': 'LGPL-3',
    'website': "https://www.dafe.es",
    'external_dependencies': {
        'python': ['requests'],
    },
    'data': [
        'data/stock_sequence_data.xml',
        'data/imei_api_config_data.xml',
        'views/res_config_settings_views.xml',
        'views/quality_check_views.xml',
    ],
    'assets': {
        'web.assets_backend': []
    },
    'images': ['static/description/icon.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
