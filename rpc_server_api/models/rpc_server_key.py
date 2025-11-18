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

from odoo import fields, models, api


class RPCServerKey(models.Model):
    _name = 'rpc.server.key'
    _description = 'RPC Server Key'

    name = fields.Char(string='Name', required=True)
    public_key_file = fields.Binary(string='Key', attachment=True)
    public_key_filename = fields.Char(string='Key Filename')
    client_user = fields.Char(string='Client')

    @api.onchange('public_key_file')
    def _onchange_public_key_file(self):
        if self.public_key_filename and '.pub' in self.public_key_filename:
            self.client_user = self.public_key_filename.replace('.pub', '')

    def rpc_key_user_show_action(self):
        pass
