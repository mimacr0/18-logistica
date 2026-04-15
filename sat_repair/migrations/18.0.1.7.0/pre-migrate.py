# -*- coding: utf-8 -*-
# Before registry load: remove obsolete ir.ui.view that referenced field "locked" on rma.repair form.
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute(
        """
        DELETE FROM ir_model_data
        WHERE (
            (module = 'rma_repair' AND name = 'rma_repair_view_form_inherit_harvest')
            OR (module = 'sat_repair' AND name = 'sat_repair_view_form_inherit_harvest')
        )
        RETURNING res_id
        """
    )
    row = cr.fetchone()
    if row and row[0]:
        vid = row[0]
        cr.execute("DELETE FROM ir_ui_view WHERE id = %s", (vid,))
        _logger.info(
            'sat_repair 18.0.1.7.0: removed obsolete view id=%s (inherit harvest).',
            vid,
        )
        return
    cr.execute(
        """
        SELECT id FROM ir_ui_view
        WHERE name = 'rma.repair.form.inherit.harvest'
        """
    )
    for (vid,) in cr.fetchall():
        cr.execute(
            "DELETE FROM ir_model_data WHERE model = 'ir.ui.view' AND res_id = %s",
            (vid,),
        )
        cr.execute("DELETE FROM ir_ui_view WHERE id = %s", (vid,))
        _logger.info(
            'sat_repair 18.0.1.7.0: removed obsolete view id=%s (rma.repair.form.inherit.harvest).',
            vid,
        )
