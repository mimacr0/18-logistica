# -*- coding: utf-8 -*-


def migrate(cr, version):
    """Move XML ids of logical package locations from rma_reception to rma_inventory (data file moved)."""
    cr.execute(
        """
        UPDATE ir_model_data
        SET module = 'rma_inventory'
        WHERE module = 'rma_reception'
          AND model = 'stock.location'
          AND name IN ('stock_location_rma_customer_final', 'stock_location_rma_unpack_zone')
        """
    )
