# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2024 DaFe Solutions
#
##############################################################################

import json
from markupsafe import Markup

from odoo import models
from odoo.http import request


class Http(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _post_logout(cls):
        super()._post_logout()
        request.future_response.set_cookie('color_scheme', max_age=0)

    def webclient_rendering_context(self):
        """ Overrides community to prevent unnecessary load_menus request """
        return {
            'session_info': self.session_info(),
        }

    def session_info(self):
        ICP = self.env['ir.config_parameter'].sudo()

        NotificationsModel = self.env['home.notifications'].sudo()

        # Ensure we get valid notifications
        notifications = NotificationsModel.get_active_notifications()

        # Make sure each notification has a valid message_style
        for notification in notifications:
            if 'message_style' not in notification or not notification['message_style']:
                notification['message_style'] = 'info'

        if self.env.user.has_group('base.group_system'):
            warn_theme = 'admin'
        elif self.env.user._is_internal():
            warn_theme = 'user'
        else:
            warn_theme = False

        result = super(Http, self).session_info()
        result['support_url'] = "https://www.odoo.com/help"

        result['home_notifications'] = notifications

        # Keep the warning flag but remove expiration details
        if warn_theme:
            result['warning'] = warn_theme
            # Set default values instead of actual expiration details
            result['expiration_date'] = '2099-12-31 23:59:59'
            result['expiration_reason'] = 'none'

        return result
