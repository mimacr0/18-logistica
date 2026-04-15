# -*- coding: utf-8 -*-
{
    'name': "SAT Repair",
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
    'version': '18.0.1.21.0',
    'depends': ['base', 'rma_base', 'rma_inventory', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/sat_repair_ticket_type_data.xml',
        'data/sat_repair_ticket_tag_data.xml',
        'data/sat_repair_ticket_category_data.xml',
        'views/sat_repair_support_views.xml',
        'views/sat_repair_views.xml',
        'views/rma_harvest_operation_views.xml',
        'views/rma_product_views.xml',
        'wizard/sat_repair_add_parts_wizard_view.xml',
        'wizard/sat_repair_harvest_wizard_view.xml',
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sat_repair/static/src/views/sat_repair_list/sat_repair_desk_state_theme.css',
            'sat_repair/static/src/views/sat_repair_list/sat_repair_list_dashboard_pipeline.xml',
            'sat_repair/static/src/views/sat_repair_list/sat_repair_list_view.xml',
            'sat_repair/static/src/views/sat_repair_list/sat_repair_list_dashboard_pipeline.js',
            'sat_repair/static/src/views/sat_repair_list/sat_repair_list_view.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,

    'license': 'LGPL-3',
}
