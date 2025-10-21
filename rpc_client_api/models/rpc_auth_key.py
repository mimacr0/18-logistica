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

import base64
import os
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from odoo import fields, models, api, _


class RPCAuthKey(models.Model):
    _name = 'rpc.auth.key'
    _description = 'RPC Auth Key'

    name = fields.Char(string='Name', required=True)
    size = fields.Selection(string='Size', selection=[
        ('2048', '2048 Bits'),
        ('4096', '4096 Bits')
    ], default='4096')
    private_key = fields.Binary(string='Private Key', attachment=True)
    private_key_filename = fields.Char(string='Key Filename')
    public_key = fields.Binary(string='Public Key', attachment=True)
    public_key_filename = fields.Char(string='Public Key Filename')


    def _generate_auth_keys(self, filename, size):
        fname = filename.lower().replace(' ', '_')
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=size,
            backend=default_backend()
        )

        # Get the private key in PEM format
        private_key_pem = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        # Get the public key in PEM format
        public_key_pem = key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        return {
            'private_key': private_key_pem,
            'public_key': public_key_pem,
            'filename': fname,
            'public_filename': f"{fname}.pub"
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            result = self._generate_auth_keys(vals['name'], int(vals.get('size') or 4096))

            vals['private_key'] = base64.b64encode(result['private_key'])
            vals['public_key'] = base64.b64encode(result['public_key'])
            vals['private_key_filename'] = result['filename']
            vals['public_key_filename'] = result['public_filename']

        return super().create(vals_list)

    def action_renew_keys(self):
        for rec in self:
            result = self._generate_auth_keys(rec.name, int(rec.size))

            rec.write({
                'private_key': False,
                'public_key': False,
                'private_key_filename': False,
                'public_key_filename': False
            })
            rec.private_key = base64.b64encode(result['private_key'])
            rec.public_key = base64.b64encode(result['public_key'])
            rec.private_key_filename = result['filename']
            rec.public_key_filename = result['public_filename']
