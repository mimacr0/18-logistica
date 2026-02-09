# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2025 DaFe Solutions
#
##############################################################################

from odoo import fields, models


class ProductCategoryInherit(models.Model):
    _inherit = 'product.category'

    name = fields.Char(string='Name', index='trigram', required=True, translate=True)
