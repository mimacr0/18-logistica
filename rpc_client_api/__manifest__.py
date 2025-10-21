##############################################################################
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
    'name': 'RPC Client API',
    'version': '18.0.1.0.0',
    'author': 'Mimacro Dev Team',
    'website': 'https://mimacro.com',
    'license': 'AGPL-3',
    'category': 'Extra Tools',
    'summary': 'RPC Client API Module',
    'depends': ['web'],
    'external_dependencies': {
        'python': ['jwt', 'cryptography']
    },
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings.xml',
        'views/rpc_client_connection.xml',
        'views/rpc_auth_key.xml',
        'views/menu.xml'
    ]
}
