# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2024 DaFe Solutions
#
##############################################################################

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pwa_app_name = fields.Char('PWA App Name', related='company_id.pwa_app_name', readonly=False)
    web_app_icon_192_pwa = fields.Binary('Image 192px', related='company_id.web_app_icon_192_pwa', readonly=False)
    web_app_icon_512_pwa = fields.Binary('Image 512px', related='company_id.web_app_icon_512_pwa', readonly=False)
    web_app_icon_192_pwa_frontend = fields.Binary('Frontend Image 192px', related='company_id.web_app_icon_192_pwa_frontend', readonly=False)
    web_app_icon_512_pwa_frontend = fields.Binary('Frontend Image 512px', related='company_id.web_app_icon_512_pwa_frontend', readonly=False)