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
