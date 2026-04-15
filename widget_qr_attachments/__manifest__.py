# -*- coding: utf-8 -*-
{
    'name': "Widget QR Attachments",
    'category': 'Extra Tools',
    'version': '18.0.1.0.0',
    'author': 'Dafe Solutions LLC',
    'maintainer': 'DaFe Solutions',
    'website': "https://www.dafe.es",
    'description': """
        Module to add a QR code widget to Odoo form views.
        Scanning the QR code opens a simple interface to upload images or files
        directly to the record from a mobile device.
    """,
    'summary': """QR Widget to attach files from mobile devices""",
    'depends': ['web', 'base'],
    'data': [
        'security/ir.model.access.csv',
        'views/upload_template.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'widget_qr_attachments/static/src/backend/js/qr_widget.js',
            'widget_qr_attachments/static/src/backend/xml/qr_widget.xml',
            'widget_qr_attachments/static/src/backend/scss/qr_widget.scss',
        ],
        'widget_qr_attachments.assets_upload_ui': [
            'web/static/lib/bootstrap/dist/css/bootstrap.css',
            'web/static/src/libs/fontawesome/css/font-awesome.css',
            'widget_qr_attachments/static/src/frontend/scss/upload_ui.scss',
        ],
    },
    'images': ['static/description/icon.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
