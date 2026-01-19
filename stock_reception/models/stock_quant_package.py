# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.osv import expression
from datetime import datetime


class QuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    def action_view_picking(self):
        """
        Override to include pickings that reference this package via origin_package_id.
        This ensures historical package associations are visible even after unpacking.
        """
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")
        # Include origin_package_id in the search domain
        domain = [
            '|', '|',
            ('result_package_id', 'in', self.ids),
            ('package_id', 'in', self.ids),
            ('origin_package_id', 'in', self.ids),
        ]
        pickings = self.env['stock.move.line'].search(domain).mapped('picking_id')
        action['domain'] = [('id', 'in', pickings.ids)]
        return action