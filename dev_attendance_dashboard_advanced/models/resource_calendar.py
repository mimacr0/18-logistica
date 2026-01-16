# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class ResourceCalendar(models.Model):
    """Extends resource.calendar to add attendance delay time settings"""
    _inherit = 'resource.calendar'

    allowed_entry_time = fields.Float(
        string='Allowed Entry Time',
        default=8.5,
        help='Allowed entry time in decimal format (e.g., 8.5 = 8:30 AM)'
    )

    minor_delay_limit = fields.Float(
        string='Minor Delay Limit',
        default=9.0,
        help='Minor delay limit in decimal format (e.g., 9.0 = 9:00 AM)'
    )