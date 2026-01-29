# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2024 DaFe Solutions
#
##############################################################################

{
    'name': 'Logistics Security',
    'version': '18.0.1.0.0',
    'author': 'DaFe Solutions',
    'maintainer': 'DaFe Solutions',
    'description': """Security groups for logistics modules""",
    'license': 'LGPL-3',
    'website': "https://www.dafe.es",
    'summary': """Common security groups for logistics""",
    'category': 'Inventory/Inventory',
    'depends': ['base', 'quality', 'quality_control', 'stock', 'hr', 'contacts'],
    'data': [
        'security/logistics_groups.xml',
        'security/ir.model.access.csv',
        'security/stock_picking_type_rules.xml',
        'views/menu_visibility.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}

