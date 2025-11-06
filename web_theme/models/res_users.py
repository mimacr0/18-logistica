# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2024 DaFe Solutions
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.osv import expression


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def _get_login_domain(self, login):
        criteria = super()._get_login_domain(login=login)
        criteria = expression.OR([criteria, [
            '|',
            ('partner_id.mobile', '=', login),
            ('partner_id.phone', '=', login)
        ]])
        return criteria
