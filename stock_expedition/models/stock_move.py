# -*- coding: utf-8 -*-

from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _get_new_picking_values(self):
        """Pass account_partner_id from sale.order to stock.picking"""
        vals = super(StockMove, self)._get_new_picking_values()
        
        # Get account_partner_id from sale.order (for deliveries from sales)
        if not vals.get('account_partner_id'):
            sale_line = self.sale_line_id
            if sale_line and sale_line.order_id.account_partner_id:
                vals['account_partner_id'] = sale_line.order_id.account_partner_id.id
        
        return vals

