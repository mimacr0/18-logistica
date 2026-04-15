# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2026 DaFe Solutions
#
##############################################################################

{
    'name': "RMA Reception",
    'category': 'Inventory/Inventory',
    'version': '18.0.2.25',
    'author': 'Dafe Solutions LLC',
    'maintainer': 'David Fernández',
    'summary': 'Módulo de Recepción de RMA. Gestiona pallets/cajas/bultos recibidos (return.package).',
    'description': """
        Control de la puerta de entrada para la logística inversa.
        - Registra pallets, cajas y sobres antes del triage.
        - Permite escaneo rápido y asociación de fotos al bulto recibido.
    """,
    'depends': ['rma_inventory', 'delivery', 'stock_delivery', 'mail'],
    'license': 'LGPL-3',
    'website': "https://www.dafe.es",
    'data': [
        'security/ir.model.access.csv',
        'data/rma_reception_check_template_data.xml',
        'wizard/rma_reception_package_wizard_views.xml',
        'wizard/rma_reception_desk_store_wizard_views.xml',
        'views/stock_quant_package_views.xml',
        'views/rma_reception_check_template_views.xml',
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'rma_reception/static/src/utils/desk_global_scan.js',
            'rma_reception/static/src/components/package_reception.css',
            'rma_reception/static/src/components/package_search_line.xml',
            'rma_reception/static/src/components/package_search_line.js',
            'rma_reception/static/src/components/package_reception.xml',
            'rma_reception/static/src/components/package_reception.js',
            'rma_reception/static/src/components/package_unpack_desk.css',
            'rma_reception/static/src/components/package_unpack_desk_detail.xml',
            'rma_reception/static/src/components/package_unpack_desk_detail.js',
            'rma_reception/static/src/components/package_unpack_desk.xml',
            'rma_reception/static/src/components/package_unpack_desk.js',
        ],
    },
    'images': ['static/description/icon.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}