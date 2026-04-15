# -*- coding: utf-8 -*-


def migrate(cr, version):
    """Map legacy rma.unit state keys to the 5 operational states."""
    cr.execute(
        """
        UPDATE rma_unit
        SET state = 'review'
        WHERE state IN ('inspection', 'waiting_customer')
        """
    )
    cr.execute(
        """
        UPDATE rma_unit
        SET state = 'stored'
        WHERE state IN ('refurbish', 'use_for_spare_parts', 'scrap')
        """
    )
    cr.execute(
        """
        UPDATE rma_unit
        SET state = 'shipped'
        WHERE state = 'ready_to_ship'
        """
    )
    cr.execute(
        """
        UPDATE rma_unit
        SET state = 'received'
        WHERE state IS NULL OR state NOT IN ('received', 'review', 'repair', 'stored', 'shipped')
        """
    )
