# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class RmaHarvestOperation(models.Model):
    _name = 'rma.harvest.operation'
    _description = 'RMA Harvest Operation'
    _order = 'create_date desc, id desc'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        default=lambda self: _('New'),
        readonly=True,
        tracking=True,
    )
    rma_unit_id = fields.Many2one(
        'rma.unit',
        string='RMA Unit',
        required=True,
        ondelete='restrict',
        index=True,
        tracking=True,
    )
    location_id = fields.Many2one(
        'stock.location',
        string='Stock location',
        required=True,
        ondelete='restrict',
        help='Location where harvested spare parts were stocked.',
    )
    owner_id = fields.Many2one(
        related='rma_unit_id.owner_id',
        comodel_name='res.partner',
        string='Owner',
        store=True,
        readonly=True,
    )
    line_ids = fields.One2many(
        'rma.harvest.operation.line',
        'operation_id',
        string='Spare parts obtained',
    )
    line_count = fields.Integer(compute='_compute_line_count', string='Parts count')

    @api.depends('line_ids')
    def _compute_line_count(self):
        for rec in self:
            rec.line_count = len(rec.line_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('rma.harvest.operation') or _('New')
        return super().create(vals_list)

    @api.model
    def _prepare_line_vals_from_unit(self, unit):
        """Build line value dicts from the unit product template harvest definition."""
        if not unit or not unit.product_id:
            return []
        tmpl = unit.product_id.product_tmpl_id
        lines = []
        for comp in tmpl.components_ids:
            if not comp.component_tmpl_id.is_spare_parts:
                continue
            variant = comp.component_tmpl_id._get_default_variant_for_harvest()
            if not variant:
                continue
            lines.append({
                'product_id': variant.id,
                'quantity': comp.quantity,
            })
        return lines


class RmaHarvestOperationLine(models.Model):
    _name = 'rma.harvest.operation.line'
    _description = 'RMA Harvest Operation Line'

    operation_id = fields.Many2one(
        'rma.harvest.operation',
        string='Harvest',
        required=True,
        ondelete='cascade',
        index=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Spare part',
        required=True,
        domain="[('product_tmpl_id.is_spare_parts', '=', True), ('type', '!=', 'service')]",
    )
    quantity = fields.Float(
        string='Quantity',
        default=1.0,
        required=True,
        digits='Product Unit of Measure',
    )
    product_uom_id = fields.Many2one(
        related='product_id.uom_id',
        string='Unit of measure',
        readonly=True,
    )
