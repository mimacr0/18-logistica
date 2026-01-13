# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2025 DaFe Solutions
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    allowed_location_ids = fields.Many2many(
        comodel_name='stock.location',
        related='picking_type_id.allowed_location_ids',
        string='Ubicaciones origen permitidas',
    )

    allowed_location_dest_ids = fields.Many2many(
        comodel_name='stock.location',
        related='picking_type_id.allowed_location_dest_ids',
        string='Ubicaciones destino permitidas',
    )


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def _check_available_quantity(self, vals):
        """
        Check if there is enough available quantity in the source location.
        For internal transfers, this prevents creating negative quants.
        
        Returns tuple: (is_valid, error_message)
        """
        picking_id = vals.get('picking_id')
        if not picking_id:
            return True, None
        
        picking = self.env['stock.picking'].browse(picking_id)
        
        # Only validate for internal transfers
        if picking.picking_type_code != 'internal':
            return True, None
        
        location_id = vals.get('location_id')
        product_id = vals.get('product_id')
        quantity = vals.get('quantity', 0)
        package_id = vals.get('package_id')
        lot_id = vals.get('lot_id')
        
        if not location_id or not product_id:
            return True, None
        
        # Skip if quantity is 0 or negative
        if float_compare(quantity, 0, precision_digits=2) <= 0:
            return True, None
        
        product = self.env['product.product'].browse(product_id)
        location = self.env['stock.location'].browse(location_id)
        
        # Get available quantity considering package and lot
        # Use strict=False to not require exact owner match (owner is set later in create)
        available_qty = self.env['stock.quant']._get_available_quantity(
            product,
            location,
            lot_id=self.env['stock.lot'].browse(lot_id) if lot_id else None,
            package_id=self.env['stock.quant.package'].browse(package_id) if package_id else None,
            owner_id=None,  # Don't filter by owner - it gets set later
            strict=False,  # Allow matching quants with any owner
        )
        
        if float_compare(quantity, available_qty, precision_rounding=product.uom_id.rounding) > 0:
            # Build descriptive error message
            location_name = location.complete_name
            product_name = product.display_name
            
            extra_info = []
            if package_id:
                package = self.env['stock.quant.package'].browse(package_id)
                extra_info.append(_("Package: %s", package.name))
            if lot_id:
                lot = self.env['stock.lot'].browse(lot_id)
                extra_info.append(_("Lot/Serial: %s", lot.name))
            
            extra_str = " (" + ", ".join(extra_info) + ")" if extra_info else ""
            
            error_msg = _(
                "Insufficient quantity for '%(product)s' in '%(location)s'%(extra)s.\n"
                "Available: %(available).2f, Requested: %(requested).2f",
                product=product_name,
                location=location_name,
                extra=extra_str,
                available=available_qty,
                requested=quantity,
            )
            return False, error_msg
        
        return True, None

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to:
        1. Validate available quantity for internal transfers
        2. Propagate owner_id from source quant for internal transfers.
        
        This fixes issues where:
        - Barcode scanning doesn't preserve the owner
        - Users can create negative quants by moving more than available
        """
        # First, validate quantities for internal transfers
        for vals in vals_list:
            is_valid, error_msg = self._check_available_quantity(vals)
            if not is_valid:
                raise UserError(error_msg)
        
        # Then, propagate owner_id
        for vals in vals_list:
            # Only process if no owner is set and we have the required data
            if vals.get('owner_id'):
                continue  # Owner already set, skip
            
            picking_id = vals.get('picking_id')
            if not picking_id:
                continue
            
            picking = self.env['stock.picking'].browse(picking_id)
            
            # Only apply to internal transfers
            if picking.picking_type_code != 'internal':
                continue
            
            # Priority 1: Use picking's account_partner_id.partner_id if available
            if hasattr(picking, 'account_partner_id') and picking.account_partner_id:
                vals['owner_id'] = picking.account_partner_id.partner_id.id
                continue
            
            # Priority 2: Use picking's owner_id if set
            if picking.owner_id:
                vals['owner_id'] = picking.owner_id.id
                continue
            
            # Priority 3: Search quant for owner
            location_id = vals.get('location_id')
            product_id = vals.get('product_id')
            lot_id = vals.get('lot_id')
            
            if not location_id or not product_id:
                continue
            
            # Search for quants with owner in the source location
            domain = [
                ('location_id', '=', location_id),
                ('product_id', '=', product_id),
                ('quantity', '>', 0),
                ('owner_id', '!=', False),
            ]
            if lot_id:
                # For tracked products, filter by lot
                domain.append(('lot_id', '=', lot_id))
            
            # Search all matching quants and pick the one with most quantity
            quants = self.env['stock.quant'].search(domain, order='quantity desc')
            
            if quants:
                # Check if all quants have the same owner
                owners = quants.mapped('owner_id')
                if len(owners) == 1:
                    vals['owner_id'] = owners[0].id
                else:
                    # Multiple owners - use the one with most quantity
                    vals['owner_id'] = quants[0].owner_id.id
        
        return super().create(vals_list)

