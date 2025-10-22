# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, fields, models
from odoo.http import request


class UserSelection(models.Model):
    """
        class for a wizard for users selection
        _onchange_user_id:
            function to get corresponding user group
        action_switch:
            function for switching the user
    """
    _name = 'user.selection'
    _description = 'User Selection'

    user_id = fields.Many2one('res.users', string="User",
                              required=True,
                              help="Select the user here",
                              domain=lambda self: [
                                  ('id', '!=', self.env.user.id)])
    access_ids = fields.One2many('res.groups',
                                 'user_id',
                                 help="User groups for the selection",
                                 string="Group", readonly=True)
    user_type = fields.Selection([('manager', 'Manager'), ('portal', 'Portal')], string="Tipo de Usuario", help="Tipo de acceso del usuario seleccionado", default='manager')


    @api.onchange('user_id')
    def _onchange_user_id(self):
        """
            Summary:
                change function to get users access group
        """
        self.access_ids = self.user_id.groups_id

    def action_switch(self):
        """
        Summary:
            function for switching the user
        Return:
            Main login page after logged in
        """
        self.ensure_one()
        session = request.session
        session.update({
            'previous_user': self.env.user.id,
        })
        session.authenticate_without_password(self.env.cr.dbname,
                                              self.user_id.login, self.env)
        return {
            'type': 'ir.actions.act_url',
            'url': '/',
            'target': 'self'
        }

    @api.model
    def default_get(self, fields):
        """Obtiene valores predeterminados desde el contexto"""
        res = super(UserSelection, self).default_get(fields)
        # Tomar el tipo de usuario del contexto si está presente
        if self._context.get('user_type'):
            res['user_type'] = self._context.get('user_type')
        # Tomar el ID de usuario del contexto si está presente
        if self._context.get('user_id'):
            res['user_id'] = self._context.get('user_id')
        return res