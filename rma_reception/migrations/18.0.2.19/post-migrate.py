# -*- coding: utf-8 -*-


def migrate(cr, version):
    """Align received_qty with declared quantity for rows created before this field existed."""
    cr.execute(
        """
        UPDATE rma_package_line
        SET received_qty = COALESCE(quantity, 1)
        """
    )
