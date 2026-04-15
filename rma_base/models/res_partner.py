# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    pricelist_item_ids = fields.One2many(
        related='property_product_pricelist.item_ids',
        readonly=True,
        string='Pricelist rules',
    )
