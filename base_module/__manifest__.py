# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2024 DaFe Solutions
#
##############################################################################

{
    'name': "Base Module ",
    'category': 'All',
    'version': '18.0.1.0.0',
    'author': 'DaFe Solutions',
    'maintainer': 'Programador 1, Programador 2',
    'description': """Base para crear nuevos módulos de Odoo""",
    'summary': """
        Este es un ejemplo de como debería ser una descripción de un módulo
        - Los cambios del frontend deben ir en las carpetas 'controllers' y 'portal'
        - Los cambios del backend deben ir en las carpetas 'models' y 'views'
        - Para elementos avanzados en JS se debe añadir la Logica en la carpeta 'static/src',
          donde tendremos una carpeta para el JS 'static/src/js', otra para los QWeb 'static/src/xml'
          y otra para los estilos 'static/src/scss'.
    """,
    'depends': ['base'],
    'license': 'LGPL-3',
    'website': "https://www.dafe.es",
    'data': [
        'data/base_data.xml',
        'security/base_security.xml',
        'views/base_views.xml',
        'report/base_report.xml',
        'wizard/base_wizard_views.xml',
        'portal/base_template.xml',
        'security/ir.model.access.csv',
    ],     # Es importante tener en cuenta el orden en el que deben declararse las carpetas y archivos
    'assets': {
        'web.assets_backend': [
            'base_module/static/src/backend/js/**.js',
            'base_module/static/src/backend/xml/**.xml',
            'base_module/static/src/backend/scss/**.scss',
        ],
        'web.assets_frontend': [
            'base_module/static/src/frontend/js/**.js',
            'base_module/static/src/frontend/xml/**.xml',
            'base_module/static/src/frontend/scss/**.scss',
        ],
    },
    'images': ['static/description/icon.png'],
    'installable': False, #Este campo se debe cambiar a True cuando se quiera que el modulo sea instalable
    'auto_install': False,
    'application': False,
}