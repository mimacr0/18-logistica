{
    'name': 'Widget Responsive Selector',
    'version': '18.0.1.0.0',
    'category': 'Web/Widgets',
    'summary': 'Custom responsive selection widget for cards/icons',
    'description': """
        This module adds a new widget 'responsive_selection' for selection and many2one fields,
        rendering options as responsive cards with icons.
    """,
    'author': 'RGB Shine',
    'depends': ['web'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            'widget_responsive_selector/static/src/views/fields/responsive_selector/responsive_selector_field.scss',
            'widget_responsive_selector/static/src/views/fields/responsive_selector/responsive_selector_field.js',
            'widget_responsive_selector/static/src/views/fields/responsive_selector/responsive_selector_field.xml',
        ],
    },
    'license': 'LGPL-3',
}
