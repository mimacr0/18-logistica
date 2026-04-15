# -*- coding: utf-8 -*-
from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_spare_parts = fields.Boolean(string='Is a Spare Part', default=False)
    components_ids = fields.One2many(
        'rma.product.template.harvest.line',
        'product_tmpl_id',
        string='Harvest components',
        help='Parts and quantities obtained when harvesting (dismantling) one unit of this product.',
    )

    def _get_default_variant_for_harvest(self):
        """Return a product.product to use when stocking a harvest line for this template."""
        self.ensure_one()
        if self.product_variant_count == 1:
            return self.product_variant_id
        return self.product_variant_ids[:1]
