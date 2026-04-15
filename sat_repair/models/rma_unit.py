# -*- coding: utf-8 -*-
from odoo import models, fields, api


class RmaUnit(models.Model):
    _inherit = 'rma.unit'

    harvest_operation_ids = fields.One2many(
        'rma.harvest.operation',
        'rma_unit_id',
        string='Harvest operations (repair)',
    )
    harvest_operation_count = fields.Integer(
        compute='_compute_harvest_operation_count',
        string='Harvest operations',
    )

    @api.depends('harvest_operation_ids')
    def _compute_harvest_operation_count(self):
        for record in self:
            record.harvest_operation_count = len(record.harvest_operation_ids)
