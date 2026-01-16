# -*- coding: utf-8 -*-

import requests
from odoo import models, fields, api
from odoo.exceptions import UserError

SSO_BASE_URL_PARAM = 'sso_redirect.base_url'


class ResUsers(models.Model):
    _inherit = 'res.users'

    token = fields.Char("Token", readonly=True, copy=False)


