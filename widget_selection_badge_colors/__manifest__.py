# -*- coding: utf-8 -*-
{
    'name': 'Widget Selection Badge Colors',
    'version': '18.0.1.0.0',
    'category': 'Web',
    'summary': 'Add color support to selection_badge widget',
    'description': """
        Allows defining custom colors for selection_badge widget options via 'colors' option.
    """,
    'author': 'Dafe Solutions LLC',
    'website': "https://www.dafe.es",
    'depends': ['web'],
    'assets': {
        'web.assets_backend': [
            'widget_selection_badge_colors/static/src/views/fields/badge_selection/badge_selection_field.scss',
            'widget_selection_badge_colors/static/src/views/fields/badge_selection/badge_selection_field_patch.js',
            'widget_selection_badge_colors/static/src/views/fields/badge_selection/badge_selection_field_patch.xml',
        ],
    },
    'images': ['static/description/icon.png'],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
