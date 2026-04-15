# -*- coding: utf-8 -*-
# Fill account_product_map_id from backed-up product + owner; drop temp columns.
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute(
        """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'rma_unit'
        )
        """
    )
    if not cr.fetchone()[0]:
        return
    cr.execute(
        """
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'rma_unit'
          AND column_name = 'migration_tmp_product_id'
        """
    )
    if not cr.fetchone():
        return
    cr.execute(
        """
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'rma_unit'
          AND column_name = 'account_product_map_id'
        """
    )
    if not cr.fetchone():
        return
    cr.execute(
        """
        UPDATE rma_unit ru
        SET account_product_map_id = sub.apm_id
        FROM (
            SELECT DISTINCT ON (ru.id) ru.id AS ru_id, apm.id AS apm_id
            FROM rma_unit ru
            INNER JOIN account_product_map apm
                ON apm.product_id = ru.migration_tmp_product_id AND apm.active = true
            INNER JOIN account_partner ap ON ap.id = apm.account_id
            WHERE ru.migration_tmp_product_id IS NOT NULL
              AND ru.migration_tmp_owner_id IS NOT NULL
              AND ap.partner_id = ru.migration_tmp_owner_id
              AND (ru.account_product_map_id IS NULL)
            ORDER BY ru.id, apm.id
        ) sub
        WHERE ru.id = sub.ru_id
        """
    )
    cr.execute(
        """
        SELECT COUNT(*) FROM rma_unit
        WHERE account_product_map_id IS NULL
          AND (migration_tmp_product_id IS NOT NULL OR migration_tmp_owner_id IS NOT NULL)
        """
    )
    n = cr.fetchone()[0]
    if n:
        _logger.warning(
            'rma_inventory 18.0.3.0.0: %s rma_unit rows still without account_product_map_id '
            '(no matching account.product.map for product+owner). Fix manually.',
            n,
        )
    cr.execute("ALTER TABLE rma_unit DROP COLUMN IF EXISTS migration_tmp_product_id")
    cr.execute("ALTER TABLE rma_unit DROP COLUMN IF EXISTS migration_tmp_owner_id")
