##############################################################################
#
# Copyright 2025 DaFe Solutions
#
##############################################################################

from odoo import models, fields


class QualityAlertTeam(models.Model):
    _inherit = 'quality.alert.team'

    leader_id = fields.Many2one(
        'res.users',
        string='Team Leader',
        help='Leader/responsible of this quality team. Only users from After Sales Department can be assigned.'
    )
    member_ids = fields.Many2many(
        'res.users',
        'quality_alert_team_member_rel',
        'team_id',
        'user_id',
        string='Team Members',
        help='Members of this quality team. Only users from After Sales Department can be added.'
    )

