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
    'name': 'Stock Expedition',
    'version': '18.0.1.0.0',
    'author': 'DaFe Solutions',
    'maintainer': 'DaFe Solutions',
    'description': """Modulo para la gestión de expediciones""",
    'summary': """Expediciones""",
    'depends': ['sale', 'product_sales_by_location'],
    'license': 'LGPL-3',
    'website': "https://www.dafe.es",
    'data': [
        'security/ir.model.access.csv',
        'views/stock_picking_type_views.xml',
        'views/stock_picking_views.xml',
        'views/sale_order_views.xml',
        'views/menu.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
    'post_init_hook': 'post_init_hook',
}
