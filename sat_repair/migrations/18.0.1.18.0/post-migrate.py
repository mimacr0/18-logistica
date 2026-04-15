# -*- coding: utf-8 -*-
"""Renombre técnico de módulo rma_repair → sat_repair (metadatos en BD)."""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute(
        """
        UPDATE ir_module_module
        SET name = 'sat_repair'
        WHERE name = 'rma_repair'
        """
    )
    if cr.rowcount:
        _logger.info(
            "sat_repair 18.0.1.18.0: ir_module_module renombrado rma_repair → sat_repair (%s filas).",
            cr.rowcount,
        )
    cr.execute(
        """
        UPDATE ir_model_data
        SET module = 'sat_repair'
        WHERE module = 'rma_repair'
        """
    )
    if cr.rowcount:
        _logger.info(
            "sat_repair 18.0.1.18.0: ir_model_data.module actualizado (%s filas).",
            cr.rowcount,
        )
