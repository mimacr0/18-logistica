# models/stock_move.py

from odoo import models

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _get_new_picking_values(self):
        vals = super(StockMove, self)._get_new_picking_values()
        source_picking = self.move_orig_ids.mapped('picking_id')
        if source_picking:
            vals['account_partner_id'] = source_picking.account_partner_id.id
        return vals

    def _action_confirm(self, merge=False, merge_into=False):
        """
        Override to prevent merging moves in reception pickings.
        This ensures that products with the same ID create separate lines
        instead of summing quantities.
        """
        moves = super(StockMove, self)._action_confirm(merge=merge, merge_into=merge_into)
        return moves
