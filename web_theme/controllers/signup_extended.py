# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2024 DaFe Solutions
#
##############################################################################

from odoo.http import request
from odoo.addons.auth_signup.controllers.main import SIGN_UP_REQUEST_PARAMS, AuthSignupHome
SIGN_UP_REQUEST_PARAMS.update(['mobile'])


class AuthSignupHomeExtended(AuthSignupHome):

    def _prepare_signup_values(self, qcontext):
        values = super()._prepare_signup_values(qcontext=qcontext)
        values['mobile'] = qcontext.get('mobile')
        values['phone'] = qcontext.get('mobile')
        return values

    def get_auth_signup_qcontext(self):
        qcontext = super().get_auth_signup_qcontext()
        user_id = request.env['res.users'].sudo().search([
            ('login', '=', qcontext.get('login'))
        ], limit=1)
        qcontext.update({
            'mobile': user_id.mobile,
        })
        return qcontext
