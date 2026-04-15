# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    rma_move_desk_root_location_ids = fields.Many2many(
        related='company_id.rma_move_desk_root_location_ids',
        readonly=False,
        string='Root locations for the selector (move units desk)',
        domain="[('usage', 'in', ('internal', 'view', 'transit')), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )
    rma_move_desk_storage_category_include_ids = fields.Many2many(
        related='company_id.rma_move_desk_storage_category_include_ids',
        readonly=False,
        string='Move desk: include only storage categories',
    )
    rma_move_desk_storage_category_exclude_ids = fields.Many2many(
        related='company_id.rma_move_desk_storage_category_exclude_ids',
        readonly=False,
        string='Move desk: exclude storage categories',
    )
