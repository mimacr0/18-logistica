# -*- coding: utf-8 -*-
"""Copy marketplace from account.product.map to rma.unit before the field is removed from the map."""


def migrate(cr, version):
    cr.execute(
        """
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'rma_unit'
        """
    )
    if not cr.fetchone():
        return

    cr.execute(
        """
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'rma_unit'
          AND column_name = 'marketplace'
        """
    )
    if not cr.fetchone():
        cr.execute("ALTER TABLE rma_unit ADD COLUMN marketplace VARCHAR")

    cr.execute(
        """
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'account_product_map'
          AND column_name = 'marketplace'
        """
    )
    if cr.fetchone():
        cr.execute(
            """
            UPDATE rma_unit ru
            SET marketplace = m.marketplace
            FROM account_product_map m
            WHERE ru.account_product_map_id = m.id
              AND m.marketplace IS NOT NULL
              AND m.marketplace != ''
              AND (ru.marketplace IS NULL OR ru.marketplace = '')
            """
        )

    cr.execute(
        """
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'rma_unit'
          AND column_name = 'map_marketplace'
        """
    )
    if cr.fetchone():
        cr.execute(
            """
            UPDATE rma_unit
            SET marketplace = map_marketplace
            WHERE (marketplace IS NULL OR marketplace = '')
              AND map_marketplace IS NOT NULL
              AND map_marketplace != ''
            """
        )
