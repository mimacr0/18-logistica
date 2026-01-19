# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    origin_package_id = fields.Many2one(
        'stock.quant.package',
        string='Origin Package',
        help='Historical reference to the original package before unpacking. '
             'This field preserves the package association for traceability '
             'even after products have been unpacked.',
        copy=False,
    )
