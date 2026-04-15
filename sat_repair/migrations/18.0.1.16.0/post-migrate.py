# -*- coding: utf-8 -*-
"""Elimina acción cliente y menú del workdesk técnico (retirado en 18.0.1.16.0)."""

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for xmlid in (
        "rma_repair.rma_repair_menu_technician_desk",
        "rma_repair.action_rma_repair_technician_desk",
        "sat_repair.sat_repair_menu_technician_desk",
        "sat_repair.action_sat_repair_technician_desk",
    ):
        rec = env.ref(xmlid, raise_if_not_found=False)
        if rec:
            rec.unlink()
            _logger.info("sat_repair migration: removed %s", xmlid)
