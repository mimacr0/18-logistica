# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2025 DaFe Solutions
#
##############################################################################

import logging
from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare

_logger = logging.getLogger(__name__)


class GenerateSerialWizard(models.TransientModel):
    _name = 'generate.serial.wizard'
    _description = 'Generate Serial Numbers Wizard'

    def _should_validate_imei_for_product(self, product):
        """
        Check if IMEI validation is required for this product based on configured categories.
        For automatic serial generation exclusion:
        Returns True if:
        - Categories ARE configured AND product belongs to one of them or their subcategories
        Returns False if:
        - No categories are configured (allow auto-generation for all)
        - Product does NOT belong to configured categories
        """
        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        category_ids_str = IrConfigParameter.get_param('quality_control_imei.category_ids', default='')
        
        # If no categories configured, don't exclude from auto-generation
        if not category_ids_str:
            return False
        
        # Parse configured category IDs
        configured_category_ids = [int(id_str) for id_str in category_ids_str.split(',') if id_str.strip()]
        if not configured_category_ids:
            return False
        
        # Get all parent categories of the product's category (including the category itself)
        product_category = product.categ_id
        category_path = []
        current_category = product_category
        
        while current_category:
            category_path.append(current_category.id)
            current_category = current_category.parent_id
        
        # Check if any of the product's categories (or parent categories) match configured ones
        for category_id in category_path:
            if category_id in configured_category_ids:
                return True
        
        # Also check if product category is a child of any configured category
        configured_categories = self.env['product.category'].browse(configured_category_ids)
        for configured_cat in configured_categories:
            if product_category.id == configured_cat.id:
                return True
            # Check if product category is descendant of configured category
            if self._is_category_descendant(product_category, configured_cat):
                return True
        
        return False

    def _is_category_descendant(self, category, parent_category):
        """
        Check if category is a descendant of parent_category
        """
        current = category.parent_id
        while current:
            if current.id == parent_category.id:
                return True
            current = current.parent_id
        return False

    picking_id = fields.Many2one('stock.picking', string='Picking', required=True, readonly=True)
    move_line_count = fields.Integer(string='Lines Requiring Serial Numbers', compute='_compute_move_line_count')
    message = fields.Html(string='Message', compute='_compute_message')

    @api.depends('picking_id')
    def _compute_move_line_count(self):
        for wizard in self:
            count = 0
            if wizard.picking_id:
                move_lines = wizard.picking_id.move_line_ids.filtered(
                    lambda ml: ml.state not in ('done', 'cancel') and
                    ml.product_id.tracking != 'none' and
                    not ml.lot_id and not ml.lot_name and
                    not wizard._should_validate_imei_for_product(ml.product_id) and
                    float_compare(ml.quantity, 0, precision_rounding=ml.product_uom_id.rounding) > 0
                )
                count = len(move_lines)
            wizard.move_line_count = count

    @api.depends('move_line_count')
    def _compute_message(self):
        for wizard in self:
            if wizard.move_line_count > 0:
                wizard.message = _(
                    '<p><strong>%s product line(s)</strong> require Lot/Serial numbers but none have been provided.</p>'
                    '<p>Do you want to generate automated serial numbers for these products?</p>'
                ) % wizard.move_line_count
            else:
                wizard.message = _(
                    '<p>Some products require Lot/Serial numbers but none have been provided.</p>'
                    '<p>Do you want to generate automated serial numbers for these products?</p>'
                )

    def action_generate_serials(self):
        """
        Generate automated serial number TEXT for move lines without lots.
        
        IMPORTANT: This method ONLY sets the lot_name field (text field).
        It does NOT create stock.lot records. The actual lot records will be
        created by Odoo's standard validation process (_create_and_assign_production_lot).
        
        Excludes products that require IMEI validation - those must be entered manually.
        After generating, closes the wizard without validating the picking.
        """
        self.ensure_one()
        
        if not self.picking_id:
            return {'type': 'ir.actions.act_window_close'}

        # First, log all tracked products and check which ones require IMEI validation
        all_tracked_lines = self.picking_id.move_line_ids.filtered(
            lambda ml: ml.state not in ('done', 'cancel') and
            ml.product_id.tracking != 'none' and
            not ml.lot_id and not ml.lot_name and
            float_compare(ml.quantity, 0, precision_rounding=ml.product_uom_id.rounding) > 0
        )
        
        for line in all_tracked_lines:
            requires_imei = self._should_validate_imei_for_product(line.product_id)
            if requires_imei:
                _logger.info(f'Excluding product {line.product_id.display_name} (ID: {line.product_id.id}, Category: {line.product_id.categ_id.display_name}) from auto-serial generation - IMEI validation required')

        # Get move lines that need serial numbers
        # EXCLUDE products that require IMEI validation
        move_lines = all_tracked_lines.filtered(
            lambda ml: not self._should_validate_imei_for_product(ml.product_id)
        )

        _logger.info(f'Generating automatic serial number text for {len(move_lines)} product lines (excluded {len(all_tracked_lines) - len(move_lines)} IMEI products)')

        # Generate serial number TEXT for each line
        # IMPORTANT: We ONLY set lot_name (text), NOT creating stock.lot records
        generated_count = 0
        for line in move_lines:
            # Generate unique serial number using sequence or timestamp
            sequence = self.env['ir.sequence'].next_by_code('stock.lot.serial')
            if not sequence:
                # Fallback to timestamp-based serial if sequence doesn't exist
                from datetime import datetime
                sequence = datetime.now().strftime('%Y%m%d%H%M%S%f')
            
            # Format: ProductCode/SequenceNumber
            product_code = line.product_id.default_code or line.product_id.name[:10]
            serial_name = f"{product_code}/{sequence}"
            
            # ONLY SET LOT_NAME TEXT FIELD - DO NOT CREATE STOCK.LOT RECORD
            # Odoo will create the stock.lot record during validation
            line.lot_name = serial_name
            
            _logger.info(f'Set lot_name to "{serial_name}" for product {line.product_id.display_name} (lot record will be created during validation)')
            generated_count += 1
        
        # Show notification and close wizard without validating
        # User must click Validate again to complete the picking
        if generated_count > 0:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Serial Numbers Generated'),
                    'message': _('%s serial number(s) have been generated. Click Validate again to complete the transfer.') % generated_count,
                    'type': 'success',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        else:
            return {'type': 'ir.actions.act_window_close'}

    def action_cancel(self):
        """Cancel and return to picking"""
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}
