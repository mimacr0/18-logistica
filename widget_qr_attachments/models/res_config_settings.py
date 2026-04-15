# -*- coding: utf-8 -*-
from odoo import fields, models

class ResConfigSettings(osv.TransientModel if 'osv' in locals() else models.TransientModel):
    _inherit = 'res.config.settings'

    qr_external_base_url = fields.Char(
        string='QR External Base URL',
        config_parameter='widget_qr_attachments.qr_external_base_url',
        help="External URL to use for the QR code (e.g. https://repair.dafe.es). If empty, the current instance URL will be used."
    )
