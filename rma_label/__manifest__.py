# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2026 DaFe Solutions
#
##############################################################################

{
    'name': "RMA Label",
    'category': 'All',
    'version': '18.0.1.0.0',
    'author': 'Dafe Solutions LLC',
    'maintainer': 'DaFe Solutions',
    'description': """Modulo para la gestión de etiquetas RMA y portal de clientes""",
    'summary': """
        Módulo para la impresión y gestión de etiquetas en el proceso RMA, con portal para clientes.
    """,
    'depends': ['base', 'rma_base', 'rma_reception', 'portal'],
    'license': 'LGPL-3',
    'website': "https://www.dafe.es",
    'data': [
        'views/portal_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'rma_label/static/src/js/portal_rma_label.js',
        ],
    },
    'images': ['static/description/icon.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
