# -*- coding: utf-8 -*-
# Backup legacy columns before rma.unit switches product_id/owner_id to related fields.


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
        cr.execute("ALTER TABLE rma_unit ADD COLUMN migration_tmp_product_id INTEGER")
    cr.execute(
        """
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'rma_unit'
          AND column_name = 'migration_tmp_owner_id'
        """
    )
    if not cr.fetchone():
        cr.execute("ALTER TABLE rma_unit ADD COLUMN migration_tmp_owner_id INTEGER")
    cr.execute(
        """
        UPDATE rma_unit
        SET migration_tmp_product_id = product_id
        WHERE migration_tmp_product_id IS NULL AND product_id IS NOT NULL
        """
    )
    cr.execute(
        """
        UPDATE rma_unit
        SET migration_tmp_owner_id = owner_id
        WHERE migration_tmp_owner_id IS NULL AND owner_id IS NOT NULL
        """
    )
