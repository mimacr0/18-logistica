# -*- coding: utf-8 -*-
# Before schema update: clear legacy harvested state and lock flag.
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute(
        """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'rma_repair'
        )
        """
    )
    if not cr.fetchone()[0]:
        return
    cr.execute(
        """
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'rma_repair'
          AND column_name = 'state'
        """
    )
    if cr.fetchone():
        cr.execute("UPDATE rma_repair SET state = 'confirmed' WHERE state = 'harvested'")
        n = cr.rowcount
        if n:
            _logger.info('sat_repair 18.0.1.4.0: updated %s repair(s) from harvested to confirmed.', n)
    cr.execute(
        """
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'rma_repair'
          AND column_name = 'locked'
        """
    )
    if cr.fetchone():
        cr.execute("UPDATE rma_repair SET locked = false WHERE locked = true")
