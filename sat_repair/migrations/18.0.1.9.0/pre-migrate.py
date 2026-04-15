# -*- coding: utf-8 -*-
# repair.operation.line: product_id removed in favor of account_product_map_id; old rows cannot be migrated safely.
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute(
        """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'repair_operation_line'
        )
        """
    )
    if not cr.fetchone()[0]:
        return
    cr.execute("SELECT COUNT(*) FROM repair_operation_line")
    n = cr.fetchone()[0]
    if n:
        cr.execute("DELETE FROM repair_operation_line")
        _logger.warning(
            'sat_repair 18.0.1.9.0: removed %s repair operation line(s) (schema change: product.product → account.product.map).',
            n,
        )
