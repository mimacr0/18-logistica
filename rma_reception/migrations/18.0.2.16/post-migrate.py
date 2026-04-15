# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    """Archive legacy demo checklist templates replaced by reception-incident set."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    for xmlid in (
        'rma_reception.rma_reception_check_template_box',
        'rma_reception.rma_reception_check_template_units',
        'rma_reception.rma_reception_check_template_labels',
    ):
        rec = env.ref(xmlid, raise_if_not_found=False)
        if rec:
            rec.write({'active': False})
