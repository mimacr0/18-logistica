# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2026 DaFe Solutions
#
##############################################################################

{
    'name': "RMA Reception",
    'category': 'Inventory/Inventory',
    'version': '18.0.1.0.0',
    'author': 'Dafe Solutions LLC',
    'maintainer': 'David Fernández',
    'summary': 'Módulo de Recepción de RMA. Gestiona pallets/cajas/bultos recibidos (return.package).',
    'description': """
        Control de la puerta de entrada para la logística inversa.
        - Registra pallets, cajas y sobres antes del triage.
        - Permite escaneo rápido y asociación de fotos al bulto recibido.
    """,
    'depends': ['rma_inventory', 'delivery', 'stock_delivery'],
    'license': 'LGPL-3',
    'website': "https://www.dafe.es",
    'data': [
        'security/ir.model.access.csv',
        'views/return_package_views.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}