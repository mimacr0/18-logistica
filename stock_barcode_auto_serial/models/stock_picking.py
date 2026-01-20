# -*- coding: utf-8 -*-

from odoo import models, fields, _
from odoo.tools.float_utils import float_compare
from odoo.exceptions import UserError


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    require_scan_confirmation = fields.Boolean(
        string='Require Scan Confirmation',
        default=False,
        help='If enabled, all lines must be scanned/confirmed (picked=True) before validating in barcode.'
    )
    show_print_lot_labels = fields.Boolean(
        string='Show Print Lot Labels Button',
        default=False,
        help='If enabled, the "Print Barcodes" button will be visible in the barcode app.'
    )

    def _get_barcode_config(self):
        """Extend barcode config with print lot labels visibility."""
        config = super()._get_barcode_config()
        config['show_print_lot_labels'] = self.show_print_lot_labels
        return config


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _should_exclude_from_auto_serial(self, product):
        """
        Hook method to determine if a product should be excluded from auto-serial generation.
        
        By default returns False (no exclusions).
        Other modules (like quality_control_imei) can override this to exclude
        products that need manual serial entry (e.g., IMEI products).
        
        :param product: product.product record
        :return: True if product should be excluded from auto-serial generation
        """
        return False

    def _check_unpicked_lines(self):
        """
        Check if there are lines that haven't been scanned/picked.
        Only checks if picking type has require_scan_confirmation enabled.
        
        Returns list of unpicked product names.
        """
        unpicked_products = []
        
        for picking in self:
            # Only check if require_scan_confirmation is enabled
            if not picking.picking_type_id.require_scan_confirmation:
                continue
            
            for ml in picking.move_line_ids:
                if ml.state in ('done', 'cancel'):
                    continue
                
                # Check if line has demand but is not picked
                has_demand = ml.move_id and float_compare(
                    ml.move_id.product_uom_qty, 0, 
                    precision_rounding=ml.product_uom_id.rounding
                ) > 0
                
                if has_demand and not ml.picked:
                    unpicked_products.append(ml.product_id.display_name)
        
        return unpicked_products

    def _pre_action_done_hook(self):
        """
        Override _pre_action_done_hook to check for missing serial numbers
        and show wizard for auto-generation before validation.
        Also checks for unpicked lines if require_scan_confirmation is enabled.
        
        Order of checks:
        1. Missing serials first (wizard generates serials AND marks picked=True)
        2. Unpicked lines after (in case there are still unpicked lines)
        """
        # First, check for products without serials (show wizard)
        # The wizard also marks lines as picked=True when generating serials
        pickings_without_lots = self._check_missing_lots()
        
        if pickings_without_lots:
            # Open wizard to prompt user to generate automated serial numbers
            wizard = self.env['generate.serial.wizard'].create({
                'picking_id': pickings_without_lots[0].id,
            })
            return {
                'name': _('Generate Serial Numbers'),
                'type': 'ir.actions.act_window',
                'res_model': 'generate.serial.wizard',
                'view_mode': 'form',
                'views': [(False, 'form')],
                'res_id': wizard.id,
                'target': 'new',
            }
        
        # After serials are generated, check for unpicked lines
        unpicked_products = self._check_unpicked_lines()
        if unpicked_products:
            # Limit to first 10 products to avoid huge error messages
            products_list = unpicked_products[:10]
            more_text = f"\n... and {len(unpicked_products) - 10} more" if len(unpicked_products) > 10 else ""
            raise UserError(_(
                "The following products have not been scanned/confirmed:\n\n"
                "%(products)s%(more)s\n\n"
                "Please scan or confirm all products before validating.",
                products="\n".join(f"- {p}" for p in products_list),
                more=more_text,
            ))

        # Call parent method to handle other validations
        return super(StockPicking, self)._pre_action_done_hook()

    def _check_missing_lots(self):
        """
        Check for move lines with serial tracking that don't have serial numbers.
        Only checks products with tracking='serial' (lot tracking is not used).
        
        Uses _should_exclude_from_auto_serial() hook to allow other modules
        to exclude certain products (e.g., IMEI products).
        
        Also checks for lines with demand but no quantity done (not yet picked/scanned).
        """
        pickings_without_lots = self.browse()

        for picking in self:
            # Only check pickings that use create or existing lots
            if not (picking.picking_type_id.use_create_lots or picking.picking_type_id.use_existing_lots):
                continue

            # Get move lines that need to be checked
            move_lines = picking.move_line_ids.filtered(
                lambda ml: ml.state not in ('done', 'cancel')
            )

            for ml in move_lines:
                # Only check products with serial tracking
                if ml.product_id.tracking != 'serial':
                    continue

                # Check if lot/serial is already provided
                if ml.lot_id or ml.lot_name:
                    continue

                # Check hook for exclusions (e.g., IMEI products)
                if self._should_exclude_from_auto_serial(ml.product_id):
                    continue

                # Check exclusions (same logic as _exclude_requiring_lot)
                picking_type_id = ml.move_id.picking_type_id
                if ml.is_inventory or ml.move_id.scrap_id:
                    continue

                # If both checkboxes are disabled, allow without lot
                if picking_type_id and not picking_type_id.use_create_lots and not picking_type_id.use_existing_lots:
                    continue

                # Check if line has quantity done OR has demand (not yet picked)
                qty_done = float_compare(ml.quantity, 0, precision_rounding=ml.product_uom_id.rounding) > 0
                has_demand = ml.move_id and float_compare(ml.move_id.product_uom_qty, 0, precision_rounding=ml.product_uom_id.rounding) > 0
                
                if qty_done or has_demand:
                    pickings_without_lots |= picking
                    break  # No need to check other lines in this picking

        return pickings_without_lots

    def check_needs_auto_serial(self):
        """
        RPC method called from barcode JS to check if there are lines
        that need automatic serial generation.
        
        This is called AFTER save() so scanned lot_names are already in the DB.
        
        Returns dict with:
        - 'needs_wizard': True if wizard should be opened
        """
        self.ensure_one()
        pickings_without_lots = self._check_missing_lots()
        return {
            'needs_wizard': bool(pickings_without_lots),
        }

    def action_print_lot_labels(self):
        """Print serial number labels directly (one per serial)."""
        self.ensure_one()
        lots = self.move_line_ids.filtered(lambda ml: ml.lot_id).mapped('lot_id')
        if not lots:
            raise UserError(_('No lots/serial numbers found to print labels.'))
        print(lots)
        account_name = self.account_partner_id.name if self.account_partner_id else ''
        # In case we want to print the barcode labels
        # report = self.env.ref('stock_barcode_auto_serial.action_report_lot_label_barcode')
        # In case we want to print the QR labels
        report = self.env.ref('stock_barcode_auto_serial.action_report_lot_label_qr')
        return report.report_action(lots.ids, data={'account_name': account_name})
