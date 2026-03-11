# -*- coding: utf-8 -*-
from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_spare_parts = fields.Boolean(string='Is a Spare Part', default=False)
