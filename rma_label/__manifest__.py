# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2026 DaFe Solutions
#
##############################################################################

{
    'name': "RMA Label",
    'category': 'All',
    'version': '18.0.1.1.8',
    'author': 'Dafe Solutions LLC',
    'maintainer': 'DaFe Solutions',
    'description': """Modulo para la gestión de etiquetas RMA y portal de clientes""",
    'summary': """
        Módulo para la impresión y gestión de etiquetas en el proceso RMA, con portal para clientes.
    """,
    'depends': ['base', 'web', 'rma_base', 'rma_inventory', 'rma_reception', 'portal'],
    'license': 'LGPL-3',
    'website': "https://www.dafe.es",
    'data': [
        'views/portal_templates.xml',
        'views/rma_unit_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'rma_label/static/src/js/portal_rma_label.js',
        ],
        'web.assets_backend': [
            # JsBarcode / QRCode / jsPDF: NO en el bundle (UMD usaría exports y no rellena window.*).
            # Se cargan en runtime con loadJS en rma_unit_label_canvas.js
            'rma_label/static/src/css/rma_unit_label_canvas.css',
            'rma_label/static/src/xml/rma_unit_label_canvas.xml',
            'rma_label/static/src/js/rma_unit_label_canvas.js',
        ],
    },
    'images': ['static/description/icon.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
