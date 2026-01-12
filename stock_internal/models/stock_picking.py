# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2025 DaFe Solutions
#
##############################################################################

from odoo import models, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    allowed_location_ids = fields.Many2many(
        comodel_name='stock.location',
        related='picking_type_id.allowed_location_ids',
        string='Ubicaciones origen permitidas',
    )

    allowed_location_dest_ids = fields.Many2many(
        comodel_name='stock.location',
        related='picking_type_id.allowed_location_dest_ids',
        string='Ubicaciones destino permitidas',
    )

