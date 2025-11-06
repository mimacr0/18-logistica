# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2024 DaFe Solutions
#
##############################################################################

{
    'name': 'Web Theme',
    'category': 'Hidden',
    'version': '18.0.2.0.0',
    'description': """
Odoo Web Theme.
===========================

This module modifies the web addon to provide custom design and responsiveness.
        """,
    'depends': ['web', 'base_setup', 'portal'],
    'data': [
        'security/ir.model.access.csv',
        'views/webclient_templates.xml',
        "views/auth_signup_login_templates.xml",
        'views/home_notifications_views.xml',
        'views/res_config_settings_views.xml',
        'views/portal_brand_views.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            ('after', 'web/static/src/scss/primary_variables.scss', 'web_theme/static/src/**/*.variables.scss'),
            ('before', 'web/static/src/scss/primary_variables.scss', 'web_theme/static/src/scss/primary_variables.scss'),
        ],
        'web._assets_secondary_variables': [
            ('before', 'web/static/src/scss/secondary_variables.scss', 'web_theme/static/src/scss/secondary_variables.scss'),
        ],
        'web._assets_backend_helpers': [
            ('before', 'web/static/src/scss/bootstrap_overridden.scss', 'web_theme/static/src/scss/bootstrap_overridden.scss'),
        ],
        'web.assets_frontend': [
            'web_theme/static/src/webclient/home_menu/home_menu_background.scss', # used by login page
            'web_theme/static/src/webclient/navbar/navbar.scss',
            'web_theme/static/src/webclient/color_scheme/color_scheme.scss',
            'web_theme/static/src/webclient/home_menu/home_notifications.scss',
            'web_theme/static/src/scss/password_eyes_icon.scss',
            'web_theme/static/src/js/password_toggle_public.js',
        ],
        'web.assets_frontend_dark': [
            ('include', 'web.dark_mode_variables'),
            'web_theme/static/src/webclient/home_menu/home_menu_background.dark.scss',
            'web_theme/static/src/webclient/home_menu/home_notifications.dark.scss',
        ],
        'web.assets_backend': [
            'web_theme/static/src/webclient/**/*.scss',
            'web_theme/static/src/views/**/*.scss',

            'web_theme/static/src/core/**/*',
            'web_theme/static/src/webclient/**/*.js',
            'web_theme/static/src/webclient/**/*.xml',
            'web_theme/static/src/views/**/*.js',
            'web_theme/static/src/views/**/*.xml',
            'web_theme/static/src/scss/password_eyes_icon.scss',
            'web_theme/static/src/js/password_eyes_icon.js',
            'web_theme/static/src/js/password_eyes_icon_field.js',
            'web_theme/static/src/xml/password_eyes_icon.xml',
            ('remove', 'web_theme/static/src/views/pivot/**'),

            # Don't include dark mode files in light mode
            ('remove', 'web_theme/static/src/**/*.dark.scss'),
        ],
        'web.assets_public': [
            'web_theme/static/src/scss/password_eyes_icon.scss',
            'web_theme/static/src/js/password_toggle_public.js',
        ],
        'web.assets_backend_lazy': [
            'web_theme/static/src/views/pivot/**',
        ],
        'web.assets_backend_lazy_dark': [
            ('include', 'web.dark_mode_variables'),
            # web._assets_backend_helpers
            ('before', 'web_theme/static/src/scss/bootstrap_overridden.scss', 'web_theme/static/src/scss/bootstrap_overridden.dark.scss'),
            ('after', 'web/static/lib/bootstrap/scss/_functions.scss', 'web_theme/static/src/scss/bs_functions_overridden.dark.scss'),
            'web_theme/static/src/webclient/home_menu/home_menu_background.dark.scss',
            'web_theme/static/src/webclient/home_menu/home_menu.dark.scss',
            'web_theme/static/src/webclient/home_menu/home_notifications.dark.scss',
        ],
        'web.assets_web': [
            ('replace', 'web/static/src/main.js', 'web_theme/static/src/main.js'),
            'web_theme/static/src/webclient/color_scheme/apply_color_scheme.js',
        ],
        # ========= Dark Mode =========
        "web.dark_mode_variables": [
            # web._assets_primary_variables
            ('before', 'web_theme/static/src/scss/primary_variables.scss', 'web_theme/static/src/scss/primary_variables.dark.scss'),
            ('before', 'web_theme/static/src/**/*.variables.scss', 'web_theme/static/src/**/*.variables.dark.scss'),
            # web._assets_secondary_variables
            ('before', 'web_theme/static/src/scss/secondary_variables.scss', 'web_theme/static/src/scss/secondary_variables.dark.scss'),
        ],
        "web.assets_web_dark": [
            ('include', 'web.dark_mode_variables'),
            # web._assets_backend_helpers
            ('before', 'web_theme/static/src/scss/bootstrap_overridden.scss', 'web_theme/static/src/scss/bootstrap_overridden.dark.scss'),
            ('after', 'web/static/lib/bootstrap/scss/_functions.scss', 'web_theme/static/src/scss/bs_functions_overridden.dark.scss'),
            # assets_backend
            'web_theme/static/src/**/*.dark.scss',
            'web_theme/static/src/webclient/home_menu/home_menu_background.dark.scss',
            'web_theme/static/src/webclient/home_menu/home_notifications.dark.scss',
        ],
        'web.tests_assets': [
            'web_theme/static/tests/*.js',
        ],
        "web.assets_tests": [
            "web_theme/static/tests/tours/**/*.js",
        ],
        # Unit test files
        'web.assets_unit_tests': [
            'web_theme/static/tests/**/*.test.js',
        ],
        'web.qunit_suite_tests': [
            'web_theme/static/tests/views/**/*.js',
            'web_theme/static/tests/webclient/**/*.js',
            ('remove', 'web_theme/static/tests/**/*.test.js'),
        ],
    },
    'license': 'OEEL-1',
}
