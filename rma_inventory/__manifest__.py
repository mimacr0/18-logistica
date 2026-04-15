# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2026 DaFe Solutions
#
##############################################################################

{
    'name': "RMA Inventory",
    'category': 'Inventory/Inventory',
    'version': '18.0.3.15.1',
    'author': 'Dafe Solutions LLC',
    'maintainer': 'David Fernández',
    'maintainer': 'DaFe Solutions',
    'summary': 'Motor principal de inventario RMA. Gestiona unidades físicas devueltas y su trazabilidad mediante movimientos internos.',
    'description': """
        Contiene el módulo base de RMA, este permite:
        - Gestionar unidades físicas devueltas
        - Trazabilidad mediante movimientos internos
    """,
    'depends': ['stock', 'mail', 'rma_base'],
    'license': 'LGPL-3',
    'website': "https://www.dafe.es",
    'data': [
        'data/ir_sequence_data.xml',
        'data/rma_stock_locations_data.xml',
        'data/stock_storage_category_data.xml',
        'security/rma_groups.xml',
        'security/ir.model.access.csv',
        'report/rma_unit_report.xml',
        'views/rma_views.xml',
        'wizards/rma_unit_store_wizard_views.xml',
        'wizards/rma_unit_move_desk_wizard_views.xml',
        'views/rma_unit_move_desk_actions.xml',
        'views/res_config_settings_views.xml',
        'views/stock_quant_views.xml',
        'views/stock_location_views.xml',
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'rma_inventory/static/src/components/rma_unit_move_desk.css',
            'rma_inventory/static/src/components/rma_unit_move_desk.xml',
            'rma_inventory/static/src/components/rma_unit_move_desk.js',
        ],
    },
    'images': ['static/description/icon.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}