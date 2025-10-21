# © <2025-Today> <ProoGeeks (dev@proogeeks.com)>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

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
