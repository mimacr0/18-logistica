# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2024 DaFe Solutions
#
##############################################################################

{
    'name': "Repair Module",
    'category': 'All',
    'version': '18.0.1.0.0',
    'author': 'DaFe Solutions',
    'maintainer': 'Angel Zhou Hu',
    'description': """Module to admin repairs""",
    'summary': """
        Este es un ejemplo de como debería ser una descripción de un módulo
        - Los cambios del frontend deben ir en las carpetas 'controllers' y 'portal'
        - Los cambios del backend deben ir en las carpetas 'models' y 'views'
        - Para elementos avanzados en JS se debe añadir la Logica en la carpeta 'static/src',
          donde tendremos una carpeta para el JS 'static/src/js', otra para los QWeb 'static/src/xml'
          y otra para los estilos 'static/src/scss'.
    """,
    'depends': ['base', 'client_account', 'repair', 'stock_expedition', 'logistics_security'],
    'license': 'LGPL-3',
    'website': "https://www.dafe.es",
    'data': [
        'data/repair_order_sequence.xml',
        'data/stock_location_data.xml',
        'data/stock_picking_data.xml',
        'data/quality_alert_data.xml',
        'views/quality_alert_views.xml',
        'views/repair_order_views.xml',
        'views/menu.xml',
        'views/stock_lot_views.xml',
        'views/stock_picking_views.xml',
        'wizard/repair_technician_change_wizard.xml',
        'security/ir.model.access.csv',
        'security/repair_access_override.xml',
        'security/repair_rules.xml',
    ],   
    'images': ['static/description/icon.png'],
    'installable': True, #Este campo se debe cambiar a True cuando se quiera que el modulo sea instalable
    'auto_install': False,
    'application': False,
}