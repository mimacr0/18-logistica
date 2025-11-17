# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2025 DaFe Solutions
#
##############################################################################

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    quality_imei_api_url = fields.Char(
        string="IMEI Validation API URL",
        config_parameter='quality_control_imei.api_url',
        help="URL endpoint for IMEI validation API"
    )
    quality_imei_api_key = fields.Char(
        string="IMEI API Key",
        config_parameter='quality_control_imei.api_key',
        help="API Key for authentication with IMEI validation service"
    )
    quality_imei_api_timeout = fields.Integer(
        string="API Timeout (seconds)",
        config_parameter='quality_control_imei.api_timeout',
        default=10,
        help="Timeout in seconds for API requests"
    )
    quality_imei_validation_required = fields.Boolean(
        string="IMEI Validation Required",
        config_parameter='quality_control_imei.validation_required',
        default=True,
        help="If enabled, quality checks with IMEI must be validated before passing"
    )
