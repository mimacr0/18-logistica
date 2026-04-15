# -*- coding: utf-8 -*-
from odoo import _, models


class RmaUnit(models.Model):
    _inherit = "rma.unit"

    def action_open_rma_unit_label_canvas(self):
        self.ensure_one()
        return {
            "type": "ir.actions.client",
            "tag": "rma_label.RmaUnitLabelCanvas",
            "target": "new",
            "name": _("Etiqueta unidad RMA"),
            "params": {
                "rma_unit_id": self.id,
            },
        }
