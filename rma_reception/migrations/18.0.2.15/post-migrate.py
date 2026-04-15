# -*- coding: utf-8 -*-


def migrate(cr, version):
    """Rename checklist column passed -> failed (inverted meaning: failed = not passed)."""
    table = None
    for t in ('rma_reception_check_line', 'rma_package_unpack_check_line'):
        cr.execute(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_name = %s AND column_name = 'passed'
            """,
            (t,),
        )
        if cr.fetchone():
            table = t
            break
    if not table:
        return
    cr.execute(
        """
        SELECT 1 FROM information_schema.columns
        WHERE table_name = %s AND column_name = 'failed'
        """,
        (table,),
    )
    if not cr.fetchone():
        cr.execute(
            "ALTER TABLE {} ADD COLUMN failed boolean DEFAULT false".format(table)
        )
    cr.execute("UPDATE {} SET failed = NOT COALESCE(passed, true)".format(table))
    cr.execute("ALTER TABLE {} DROP COLUMN passed".format(table))
