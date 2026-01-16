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
    'depends': ['base', 'quality', 'quality_control'],
    'data': [
        'security/logistics_groups.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}

