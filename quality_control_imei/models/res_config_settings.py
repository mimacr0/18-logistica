# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2025 DaFe Solutions
#
##############################################################################

from odoo import api, fields, models


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
    quality_imei_category_ids = fields.Many2many(
        comodel_name='product.category',
        relation='quality_imei_category_rel',
        column1='config_id',
        column2='category_id',
        string="IMEI Product Categories",
        help="Only products in these categories (or their subcategories) will require IMEI validation. Leave empty to validate all products."
    )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        category_ids_str = IrConfigParameter.get_param('quality_control_imei.category_ids', default='')
        if category_ids_str:
            category_ids = [int(id_str) for id_str in category_ids_str.split(',') if id_str.strip()]
            res['quality_imei_category_ids'] = [(6, 0, category_ids)]
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        category_ids_str = ','.join(str(id) for id in self.quality_imei_category_ids.ids)
        IrConfigParameter.set_param('quality_control_imei.category_ids', category_ids_str)
