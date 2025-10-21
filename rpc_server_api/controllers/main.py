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
import json
import jwt
import logging
from datetime import datetime, timedelta

from odoo import http, api
from odoo.http import request

_logger = logging.getLogger(__name__)


class RPCController(http.Controller):


    @http.route("/rpc/token/api/auth/token", type="json", auth="public", csrf=False, methods=["POST"], cors="*")
    def rpc_token_api_auth_token(self, **data):
        RPCIncominKey = request.env['rpc.server.key'].sudo()
        SysParams = request.env['ir.config_parameter'].sudo()
        token = request.httprequest.headers.get('Authorization')
        secret = SysParams.get_param('service.rpc.api.token.secret')

        if not token:
            return {"status": "error", "message": "Token not found", "code": 404}

        if not secret:
            _logger.error("Secret key not found in system parameters")
            return {"status": "error", "message": "Internal error", "code": 500}

        if ',' not in token:
            return {"status": "error", "message": "Invalid token format", "code": 404}

        cid, token = token.split(' ')[1].split(',')

        client = RPCIncominKey.search([('client_user', '=', cid)])

        if not client:
            return {"status": "error", "message": "Invalid client user", "code": 404}

        if not client.public_key_file:
            return {"status": "error", "message": "Invalid client key", "code": 404}

        key = base64.b64decode(client.public_key_file)

        try:
            payload = jwt.decode(token, key, algorithms=['RS256'])
            new_token = jwt.encode({ 'exp': datetime.utcnow() + timedelta(hours=8) }, secret, algorithm='HS256')
            return {"status": "success", "message": "Authentication successful", "token": new_token}
        except jwt.ExpiredSignatureError:
            return {"status": "error", "message": "Token has expired", "code": 401}
        except jwt.InvalidTokenError:
            return {"status": "error", "message": "Invalid token", "code": 404}

        return {"status": "error", "message": "Invalid token", "code": 404}

    @http.route("/rpc/token/api/ws/action", type="json", auth="public", csrf=False, methods=["POST"], cors="*")
    def rpc_token_api_ws_action(self):
        RPCIncominKey = request.env['rpc.server.key'].sudo()
        RPCAPIAction = request.env['rpc.server.action'].sudo()
        SysParams = request.env['ir.config_parameter'].sudo()
        token = request.httprequest.headers.get('Authorization')
        secret = SysParams.get_param('service.rpc.api.token.secret')
        data = json.loads(request.httprequest.data)

        if not secret:
            _logger.error("Secret key not found in system parameters")
            return {"status": "error", "message": "Internal error", "code": 500}

        token = token.replace('Bearer ', '')

        try:
            jwt.decode(token, secret, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return {"status": "error", "message": "Token has expired", "code": 401}
        except jwt.InvalidTokenError:
            return {"status": "error", "message": "Invalid token", "code": 404}

        action = RPCAPIAction.search([('reference', '=', data.get('action'))])

        if not action:
            return {"status": "error", "message": "Action not found", "code": 404}

        return action.execute(data.get('data') or {})

