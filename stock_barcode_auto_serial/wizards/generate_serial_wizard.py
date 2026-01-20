# -*- coding: utf-8 -*-

from collections import defaultdict
from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare


class GenerateSerialWizard(models.TransientModel):
    _name = 'generate.serial.wizard'
    _description = 'Generate Serial Numbers Wizard'

    picking_id = fields.Many2one('stock.picking', string='Picking', required=True, readonly=True)
    move_line_count = fields.Integer(string='Lines Requiring Serial Numbers', compute='_compute_move_line_count')
    message = fields.Html(string='Message', compute='_compute_message')

    def _should_exclude_from_auto_serial(self, product):
        """
        Hook method to determine if a product should be excluded from auto-serial generation.
        Delegates to picking's method for consistency.
        
        :param product: product.product record
        :return: True if product should be excluded
        """
        if self.picking_id:
            return self.picking_id._should_exclude_from_auto_serial(product)
        return False

    @api.depends('picking_id')
    def _compute_move_line_count(self):
        for wizard in self:
            count = 0
            if wizard.picking_id:
                move_lines = wizard.picking_id.move_line_ids.filtered(
                    lambda ml: ml.state not in ('done', 'cancel') and
                    ml.product_id.tracking == 'serial' and
                    not ml.lot_id and not ml.lot_name and
                    not wizard._should_exclude_from_auto_serial(ml.product_id)
                )
                count = len(move_lines)
            wizard.move_line_count = count

    @api.depends('move_line_count')
    def _compute_message(self):
        for wizard in self:
            if wizard.move_line_count > 0:
                wizard.message = _(
                    '<p><strong>%s product line(s)</strong> require Serial numbers but none have been provided.</p>'
                    '<p>Do you want to generate automated serial numbers for these products?</p>'
                ) % wizard.move_line_count
            else:
                wizard.message = _(
                    '<p>Some products require Serial numbers but none have been provided.</p>'
                    '<p>Do you want to generate automated serial numbers for these products?</p>'
                )

    def action_generate_serials(self):
        """
        Generate automated serial number TEXT for move lines without lots.
        
        IMPORTANT: This method ONLY sets the lot_name field (text field).
        It does NOT create stock.lot records. The actual lot records will be
        created by Odoo's standard validation process (_create_and_assign_production_lot).
        
        Uses _should_exclude_from_auto_serial() hook to allow other modules
        to exclude certain products (e.g., IMEI products).
        
        After generating, reloads the barcode view.
        """
        self.ensure_one()
        
        if not self.picking_id:
            return {'type': 'ir.actions.act_window_close'}

        # Get all serial tracked lines without lot/serial
        all_tracked_lines = self.picking_id.move_line_ids.filtered(
            lambda ml: ml.state not in ('done', 'cancel') and
            ml.product_id.tracking == 'serial' and
            not ml.lot_id and not ml.lot_name
        )

        # Get move lines that need serial numbers (excluding via hook)
        move_lines = all_tracked_lines.filtered(
            lambda ml: not self._should_exclude_from_auto_serial(ml.product_id)
        )

        if not move_lines:
            return {'type': 'ir.actions.act_window_close'}

        # Group lines by package (result_package_id, package_id, or origin_package_id)
        lines_by_package = defaultdict(list)
        for line in move_lines:
            if line.result_package_id:
                package_key = ('result', line.result_package_id.id)
            elif line.package_id:
                package_key = ('source', line.package_id.id)
            elif line.origin_package_id:
                package_key = ('origin', line.origin_package_id.id)
            else:
                package_key = ('no_package', line.picking_id.id if line.picking_id else None)
            lines_by_package[package_key].append(line)

        # Generate serial number TEXT for each line grouped by package
        generated_count = 0
        for package_key, package_lines in lines_by_package.items():
            sequence = 1
            for line in package_lines:
                # Get package name (priority: result_package_id > package_id > origin_package_id)
                if line.result_package_id and line.result_package_id.name:
                    package_name = line.result_package_id.name
                elif line.package_id and line.package_id.name:
                    package_name = line.package_id.name
                elif line.origin_package_id and line.origin_package_id.name:
                    package_name = line.origin_package_id.name
                else:
                    package_name = line.product_id.default_code or line.product_id.name[:10]
                
                serial_name = f"{package_name}-{str(sequence).zfill(3)}"
                
                # Set lot_name, quantity (if not set), and mark as picked
                vals = {
                    'lot_name': serial_name,
                    'picked': True,
                }
                if float_compare(line.quantity, 0, precision_rounding=line.product_uom_id.rounding) <= 0:
                    vals['quantity'] = 1
                
                line.write(vals)
                generated_count += 1
                sequence += 1
        
        # Reload the barcode view to show updated lines (green)
        if generated_count > 0:
            action = self.env["ir.actions.actions"]._for_xml_id("stock_barcode.stock_barcode_picking_client_action")
            action['context'] = {'active_id': self.picking_id.id}
            return action
        else:
            return {'type': 'ir.actions.act_window_close'}

    def action_cancel(self):
        """Cancel and return to picking"""
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}
