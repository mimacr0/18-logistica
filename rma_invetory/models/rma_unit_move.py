# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2026 DaFe Solutions
#
##############################################################################

from odoo import models, fields


class RmaUnitMove(models.Model):
    _name = 'rma.unit.move'
    _description = 'RMA Unit Move'

    rma_unit_id = fields.Many2one(
        "rma.unit",
        string="RMA Unit"
    )
    from_location_id = fields.Many2one(
        "stock.location",
        string="From Location"
    )
    to_location_id = fields.Many2one(
        "stock.location",
        string="To Location"
    )
    user_id = fields.Many2one(
        "res.users",
        string="User"
    )
    date = fields.Datetime(string="Date")
    reason = fields.Char(string="Reason")
