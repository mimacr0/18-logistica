# models/stock_move.py

from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _get_new_picking_values(self):
        """Pass account_partner_id from source picking (for chained moves)"""
        vals = super()._get_new_picking_values()
        source_picking = self.move_orig_ids.mapped('picking_id')
        if source_picking and source_picking.account_partner_id:
            vals['account_partner_id'] = source_picking.account_partner_id.id
        return vals

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        """
        Override to propagate origin_package_id from source move lines.
        This ensures package traceability across chained operations.
        """
        vals = super()._prepare_move_line_vals(quantity, reserved_quant)
        
        # If reserving from a quant with a package, set origin_package_id
        if reserved_quant and reserved_quant.package_id:
            vals['origin_package_id'] = reserved_quant.package_id.id
        
        # Also try to get origin_package_id from source move lines
        if not vals.get('origin_package_id') and self.move_orig_ids:
            source_move_lines = self.move_orig_ids.mapped('move_line_ids')
            if source_move_lines:
                # Get origin_package_id from source, prioritizing non-empty values
                origin_package = source_move_lines.filtered(
                    lambda ml: ml.origin_package_id
                ).mapped('origin_package_id')[:1]
                if origin_package:
                    vals['origin_package_id'] = origin_package.id
        
        return vals

    def _action_confirm(self, merge=False, merge_into=False):
        """
        Override to prevent merging moves in reception pickings.
        This ensures that products with the same ID create separate lines
        instead of summing quantities.
        """
        moves = super()._action_confirm(merge=merge, merge_into=merge_into)
        return moves
