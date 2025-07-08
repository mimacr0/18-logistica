##############################################################################
#
# Copyright 2025 DaFe Solutions
#
##############################################################################

from odoo import models, fields, api, _


class QualityCheck(models.Model):
    _inherit = 'quality.check'

    is_repair_request = fields.Boolean(string="Repair/Review Request")
    repair_order_id = fields.Many2one('repair.order', string="Associated Technical Order")
