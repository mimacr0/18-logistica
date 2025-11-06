# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2024 DaFe Solutions
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.osv import expression


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def signup_retrieve_info(self, token):
        res = super().signup_retrieve_info(token=token)
        partner = self._signup_retrieve_partner(token, raise_exception=True)
        res['mobile'] = partner.mobile or ''
        return res
