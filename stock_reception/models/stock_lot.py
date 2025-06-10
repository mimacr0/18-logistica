# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class ProductionLot(models.Model):
    _inherit = 'stock.lot'

    pakcage_id = fields.Char(
        string='Package ID',
        help='ID of the package where the lot is stored',
    )
