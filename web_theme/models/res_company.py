# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2024 DaFe Solutions
#
##############################################################################

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    pwa_app_name = fields.Char('PWA App Name')
    web_app_icon_192_pwa = fields.Binary('Image 192px')
    web_app_icon_512_pwa = fields.Binary('Image 512px')
    web_app_icon_192_pwa_frontend = fields.Binary('Frontend Image 192px')
    web_app_icon_512_pwa_frontend = fields.Binary('Frontend Image 512px')