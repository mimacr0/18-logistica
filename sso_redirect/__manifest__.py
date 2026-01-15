# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2026 DaFe Solutions
#
##############################################################################

{
    'name': "SSO Redirect",
    'summary': "SSO Redirect Controller and Menu Override",

    'description': """
        Module that provides:
        - SSO verification controller
        - Menu redirect based on SSO conditions
    """,

    'author': "Dafe Solutions LLC",
    'website': "https://www.dafe.es",
    'category': 'Tools',
    'sequence': 100,
    'version': '18.0.1.0.0',

    'depends': ['base', 'web', 'hr'],

    'data': [
        'security/ir.model.access.csv',
    ],

    'assets': {
        'web.assets_backend': [
            'sso_redirect/static/src/js/menu_redirect.js',
        ],
    },
    'license': 'LGPL-3',
    'application': False,
}

