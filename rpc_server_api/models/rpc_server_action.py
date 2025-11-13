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

from datetime import datetime
from markupsafe import Markup
from pytz import timezone
import logging

from odoo import fields, models
from odoo.tools.safe_eval import safe_eval
from odoo.addons.rpc_server_api.tools.sdict import SafeDict

_logger = logging.getLogger(__name__)


class RPCServerAction(models.Model):
    _name = 'rpc.server.action'
    _description = 'RPC Server Action'

    name = fields.Char(string='Name', required=True)
    reference = fields.Char(string='Reference', required=True)
    action = fields.Text(string='Action')


    def execute(self, data):
        self.ensure_one()

        def localized_time(dt = False, tz = 'America/Mexico_City'):
            if not dt:
                dt = datetime.now()
            dt = dt.astimezone(timezone(tz))
            return datetime.strptime(dt.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')

        def query(env, _sql):
            env.cr.execute(_sql)
            return env.cr.fetchall() or []

        ctx = {
            'log': _logger,
            'env': self.env,
            'args': SafeDict(data),
            'localized_time': localized_time,
            'query': query,
            'Markup': Markup
        }

        try:
            safe_eval(self.action, ctx, mode="exec", nocopy=True)
            return { 'status': 'success', 'data': ctx.get('result') }
        except Exception as e:
            _logger.error('Error executing action %s: %s', self.name, e)

        return { 'status': 'error', 'message': 'Error executing action' }
