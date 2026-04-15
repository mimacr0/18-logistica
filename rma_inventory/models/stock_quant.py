# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2026 DaFe Solutions
#
##############################################################################

from odoo import fields, models


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    is_spare_parts = fields.Boolean(
        related='product_id.product_tmpl_id.is_spare_parts',
        readonly=True,
    )

    account_product_map_id = fields.Many2one(
        'account.product.map',
        string='Customer product map',
        index=True,
        ondelete='set null',
        help='Client product mapping when this quant was created from RMA reception (unpack).',
    )
