# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2026 DaFe Solutions
#
##############################################################################

{
    'name': "RMA Inventory",
    'category': 'Inventory/Inventory',
    'version': '18.0.1.0.0',
    'author': 'Dafe Solutions LLC',
    'maintainer': 'David Fernández',
    'maintainer': 'DaFe Solutions',
    'summary': 'Motor principal de inventario RMA. Gestiona unidades físicas devueltas y su trazabilidad mediante movimientos internos.',
    'description': """
        Contiene el módulo base de RMA, este permite:
        - Gestionar unidades físicas devueltas
        - Trazabilidad mediante movimientos internos
    """,
    'depends': ['stock', 'mail'],
    'license': 'LGPL-3',
    'website': "https://www.dafe.es",
    'data': [
        'data/ir_sequence_data.xml',
        'security/rma_groups.xml',
        'security/ir.model.access.csv',
        'views/rma_views.xml',
    ],
    # 'assets': {
    #     'web.assets_backend': [
    #         'base_module/static/src/backend/js/**.js',
    #         'base_module/static/src/backend/xml/**.xml',
    #         'base_module/static/src/backend/scss/**.scss',
    #     ],
    #     'web.assets_frontend': [
    #         'base_module/static/src/frontend/js/**.js',
    #         'base_module/static/src/frontend/xml/**.xml',
    #         'base_module/static/src/frontend/scss/**.scss',
    #     ],
    # },
    'images': ['static/description/icon.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}