# -*- coding: utf-8 -*-
{
    'name': "RMA Repair",
    'summary': "Technical Repair Management for RMA Units",
    'description': """
        Handles the technical repair process for RMA units, including:
        - Diagnostics and results mapping.
        - Repair operations tracking.
        - Integration with rma_inventory.
    """,
    'author': "DaFe Solutions",
    'website': "https://www.dafe.es",
    'category': 'Technical/RMA',
    'version': '18.0.1.0.0',
    'depends': ['base', 'rma_base', 'rma_inventory', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/rma_repair_views.xml',
        'views/rma_product_views.xml',
        'wizard/rma_repair_add_parts_wizard_view.xml',
        'wizard/rma_repair_harvest_wizard_view.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,

    'license': 'LGPL-3',
}
