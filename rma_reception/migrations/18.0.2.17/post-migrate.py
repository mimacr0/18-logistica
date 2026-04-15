# -*- coding: utf-8 -*-


def migrate(cr, version):
    """Move legacy rma_state='incident' to received + rma_has_incident."""
    cr.execute(
        """
        UPDATE stock_quant_package
        SET rma_has_incident = TRUE, rma_state = 'received'
        WHERE rma_state = 'incident'
        """
    )
