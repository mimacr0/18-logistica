# -*- coding: utf-8 -*-


def migrate(cr, version):
    """Rename DB columns rma_state → package_state, rma_has_incident → package_has_incident."""
    cr.execute(
        """
        DO $body$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = current_schema()
                  AND table_name = 'stock_quant_package'
                  AND column_name = 'rma_state'
            ) AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = current_schema()
                  AND table_name = 'stock_quant_package'
                  AND column_name = 'package_state'
            ) THEN
                ALTER TABLE stock_quant_package RENAME COLUMN rma_state TO package_state;
            END IF;
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = current_schema()
                  AND table_name = 'stock_quant_package'
                  AND column_name = 'rma_has_incident'
            ) AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = current_schema()
                  AND table_name = 'stock_quant_package'
                  AND column_name = 'package_has_incident'
            ) THEN
                ALTER TABLE stock_quant_package RENAME COLUMN rma_has_incident TO package_has_incident;
            END IF;
        END
        $body$;
        """
    )
