##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2015 Mimacro S.L
#    (<http://mimacro.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Stock Package Reception',
    'version': '18.0.1.0.0',
    'author': 'DaFe Solutions',
    'maintainer': 'Mimacro S.L',
    'description': """Modulo para la gestión de recepción de paquetes""",
    'license': 'LGPL-3',
    'website': "https://www.dafe.es",
    'summary': """Recepción de paquetes""",
    'depends': ['stock', 'delivery', 'hr', 'contacts_menu', 'product_menu', 'stock_menu', 'package_menu', 'quality', 'quality_control', 'logistics_security'],
    'data': [
        'security/package_reception_security.xml',
        'security/ir.model.access.csv',
        'data/quality_point_data.xml',
        'wizard/create_stock_picking_wizard.xml',
        'wizard/receive_package_wizard.xml',
        'views/stock_picking_views.xml',
        'views/stock_barcode_views.xml',
        'views/stock_quant_views.xml',
        'views/stock_lot_views.xml',
        'views/quality_point_views.xml',

    ],
    "demo": [],
    'assets': {
        'web.assets_backend': [
            'stock_reception/static/src/**/*.xml',
            'stock_reception/static/src/**/*.js',
        ]
    },
    'images': ['static/description/logo.png'],
    'post_init_hook': 'post_init_hook',
}
