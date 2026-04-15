# -*- coding: utf-8 -*-


def migrate(cr, version):
    """Default template type for rows created before package-type filtering."""
    cr.execute(
        """
        UPDATE rma_unpack_check_template
        SET type = 'all'
        WHERE type IS NULL
        """
    )
