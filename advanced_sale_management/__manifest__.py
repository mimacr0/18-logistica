# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2026 DaFe Solutions
#
##############################################################################

{
    'name': "Advanced Sale Managment ",
    'category': 'All',
    'version': '18.0.1.0.0',
    'author': 'Dafe Solutions LLC',
    'maintainer': 'Programador 1, Programador 2',
    'maintainer': 'DaFe Solutions',
    'description': """Módulo para la gestión integral de ventas, logística y servicios de la empresa""",
    'summary': """
        Este módulo permite gestionar de forma centralizada todas las operaciones comerciales de la empresa:

        - Gestión de ventas de productos
        - Control de recepciones y expediciones (logística de entrada y salida)
        - Administración de servicios asociados como reparación, venta y alquiler
        - Integración de procesos comerciales y operativos en un único flujo

        Incluye soporte tanto para procesos backend como frontend:
        - Lógica de negocio en 'models' y vistas en 'views'
        - Controladores y portal para interacción web
        - Funcionalidades avanzadas en 'static/src' (JS, QWeb y SCSS)
    """,

    'depends': ['base', 'sale'],
    'license': 'LGPL-3',
    'website': "https://www.dafe.es",
    'data': [
        'views/base_views.xml',
    ],     # Es importante tener en cuenta el orden en el que deben declararse las carpetas y archivos
    'assets': {
      
    },
    'images': ['static/description/icon.png'],
    'installable': False, #Este campo se debe cambiar a True cuando se quiera que el modulo sea instalable
    'auto_install': False,
    'application': False,
}