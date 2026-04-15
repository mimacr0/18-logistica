# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2026 DaFe Solutions
#
##############################################################################

{
    'name': "Account Partner",
    'category': 'Services/Accounts',
    'version': '18.0.1.0.1',
    'author': 'DaFe Solutions',
    'maintainer': 'DaFe Solutions',
    'description': """Modulo para la gestión de clientes y cuentas en el portal""",
    'summary': """Gestión de los Contactos y los creditos de los clientes""",
    'depends': ['base', 'account', 'sale_management', 'contacts'],
    'license': 'LGPL-3',
    'website': "https://www.dafe.es",
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/mail_templates.xml',
        'wizard/reject_reason_credit_wizard.xml',
        'views/account_partner_view.xml',
        'views/res_partner_view.xml',
        'views/contact_res_partner.xml',
        'views/credit_account_view.xml',
        'wizard/add_account_partner_view.xml',
        'views/menu.xml',
        'portal/menu_portal.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'account_partner/static/src/js/add_account_partner_list.js',
            'account_partner/static/src/js/add_account_partner_list.xml',
            'account_partner/static/src/list/account_carrier_select_list_view.js',
            'account_partner/static/src/list/account_carrier_select_list_view.xml'
        ],
    },
    'images': ['static/description/icon.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}