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

import logging
import base64
import random
import requests
import string
import jwt
from datetime import datetime, timedelta

from odoo import fields, models, api, _

_logger = logging.getLogger(__name__)

def _join_url(*parts):
    _parts = [part.strip('/') for part in parts if part.strip('/')]
    return '/'.join(_parts)


class RPCClientConnection(models.Model):
    _name = 'rpc.client.connection'
    _description = 'RPC Client Connection'

    name = fields.Char(string='Name', required=True)
    client_user = fields.Char(string='Client')
    rpc_key_id = fields.Many2one(string='RPC Key', comodel_name='rpc.auth.key')
    url = fields.Char(string='URL', required=True)
    last_token = fields.Char(string='Last Token', copy=False)
    json_rpc = fields.Boolean(string='JSON RPC', default=False)
    state = fields.Selection(string='State', selection=[
        ('disconnected', 'Disconnected'),
        ('connected', 'Connected')
    ], default='disconnected')

    def action_test_connection(self):
        self.ensure_one()
        token = self._request_token()

        if not token:
            self.write({ 'last_token': None })
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'type': 'danger',
                    'message': _('Authorization failed'),
                    'next': {'type': 'ir.actions.act_window_close'}
                }
            }

        self.state = 'connected'
        self.last_token = token
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'type': 'success',
                'message': _('Connection successful'),
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }

    def generate_client_user_action(self):
        chars = string.ascii_lowercase + string.digits + string.ascii_uppercase + '_'
        self.client_user = ''.join(random.choices(chars, k=32))

    def action_download_public_key(self):
        self.ensure_one()
        key = self.rpc_key_id

        if not self.client_user:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'type': 'danger',
                    'message': 'Client user not found',
                    'next': {'type': 'ir.actions.act_window_close'}
                }
            }

        Attachment = self.env['ir.attachment'].sudo()
        attachment = Attachment.search([('res_model', '=', self._name), ('res_id', '=', self.id), ('name', 'like', '%.pub')], limit=1)

        if not attachment:
            attachment = Attachment.create({
                'name': f"{self.client_user}.pub",
                'res_model': self._name,
                'res_id': self.id,
                'datas': key.public_key.decode('utf-8'),
                'type': 'binary',
                'mimetype': 'application/x-pem-file'
            })

        if attachment.id:
            attachment.write({
                'name': f"{self.client_user}.pub",
                'datas': key.public_key.decode('utf-8')
            })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=1',
            'target': 'new'
        }

    def _process_response(self, response):
        if self.json_rpc:
            return response.get('result', {})

        return response

    def _request_token(self):
        key = base64.b64decode(self.rpc_key_id.private_key)
        payload = { 'exp': datetime.now() + timedelta(minutes=5) }
        token = jwt.encode(payload, key, algorithm='RS256')
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.client_user},{token}'
        }

        url = _join_url(self.url, 'rpc/token/api/auth/token')
        res, status_code = self._make_http_request(url, headers, {}, 'POST')

        if not str(status_code).startswith('2') or res.get('status') != 'success':
            return False

        return res.get('token')

    def _ensure_valid_token(self):
        """Ensure we have a valid token, requesting a new one if needed"""
        if not self.last_token:
            token = self._request_token()
            if not token:
                return False
            self.last_token = token
        return self.last_token

    def _get_auth_headers(self, token=None):
        """Get headers with authorization token"""
        token = token or self.last_token
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }

    def _make_http_request(self, url, headers, data=None, method='GET'):
        """Make an HTTP request and return the processed response"""
        try:
            if method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data, verify=False)
            else:
                response = requests.get(url, headers=headers, json=data, verify=False)

            try:
                res = self._process_response(response.json())
                return res, res.get('code') or response.status_code
            except Exception:
                return {'status': 'error', 'message': _('Invalid JSON response')}, 400

        except Exception as e:
            _logger.error(f"Error: {e}")
            return {'status': 'error', 'message': _('Connection error')}, 500

    def _request(self, endpoint, data=None, method='GET'):
        self.ensure_one()
        token = self._ensure_valid_token()

        if not token:
            return {
                'status': 'error',
                'message': _('Authorization failed')
            }

        url = _join_url(self.url.rstrip('/'), endpoint)
        headers = self._get_auth_headers(token)

        # Make the initial request
        res, status_code = self._make_http_request(url, headers, data, method)

        # Handle token expiration (401)
        if status_code == 401:
            token = self._request_token()
            if not token:
                _logger.error(f"Error: {res}")
                return {
                    'status': 'error',
                    'message': _('Authorization failed')
                }

            self.last_token = token
            headers = self._get_auth_headers(token)
            res, status_code = self._make_http_request(url, headers, data, method)

        # Handle not found (404)
        if status_code == 404:
            _logger.error(f"Not found: {res}")
            return {
                'status': 'error',
                'message': _('Not found')
            }

        _logger.debug(f"Response: {res}")
        return res

    def request_post(self, endpoint, data=None):
        return self._request(endpoint, data or {}, 'POST')

    def request_get(self, endpoint, data=None):
        return self._request(endpoint, data or {})

    def rpc_action(self, action, data=None):
        """
        Execute a RPC action on the remote server

        Args:
            action_reference (str): The reference/identifier of the action
            data (dict): Data to be passed to the action

        Returns:
            dict: Response from the server
        """
        return self.request_post('/rpc/token/api/ws/action', {
            'action': action,
            'data': data or {}
        })
