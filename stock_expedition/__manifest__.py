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
    'author': 'Mimacro S.L',
    'maintainer': 'Mimacro S.L',
    'website': 'http://mimacro.com',
    'license': 'AGPL-3',
    'category': 'Extra Tools',
    'summary': '',
    'depends': ['sale', 'product_sales_by_location'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',

    ],
    "demo": ['data/product_data_demo.xml'],
    'assets': {
    },
    'images': ['static/description/icon.png']
}
