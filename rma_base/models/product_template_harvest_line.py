# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RmaProductTemplateHarvestLine(models.Model):
    _name = 'rma.product.template.harvest.line'
    _description = 'Product template harvest component'
    _order = 'id'

    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Product',
        required=True,
        ondelete='cascade',
        index=True,
    )
    component_tmpl_id = fields.Many2one(
        'product.template',
        string='Component (part obtained)',
        required=True,
        ondelete='restrict',
        index=True,
        domain="[('is_spare_parts', '=', True)]",
        help='Spare-part product template obtained when harvesting one unit of the parent product.',
    )
    quantity = fields.Float(
        string='Quantity per harvest',
        default=1.0,
        required=True,
        digits='Product Unit of Measure',
    )

    _sql_constraints = [
        (
            'product_component_uniq',
            'unique(product_tmpl_id, component_tmpl_id)',
            'Each component can only be listed once per product template.',
        ),
    ]

    @api.constrains('component_tmpl_id', 'product_tmpl_id')
    def _check_not_same_template(self):
        for line in self:
            if line.component_tmpl_id == line.product_tmpl_id:
                raise ValidationError(
                    _('The harvested component cannot be the same product as the parent.')
                )

    @api.constrains('component_tmpl_id')
    def _check_component_is_spare_part(self):
        for line in self:
            if line.component_tmpl_id and not line.component_tmpl_id.is_spare_parts:
                raise ValidationError(
                    _('Harvest components must be products marked as spare parts.')
                )
