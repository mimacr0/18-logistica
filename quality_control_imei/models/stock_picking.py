# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2025 DaFe Solutions
#
##############################################################################

import logging
import requests
from markupsafe import Markup
from odoo import models, _
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

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

    def button_validate(self):
        """
        Override button_validate to check for missing serial/lot numbers and validate IMEI:
        1. First check IMEI validation products - raise error if missing serials
        2. Validate IMEI numbers via API for IMEI products
        3. Then check non-IMEI products - show wizard for auto-generation
        After user generates serials and closes wizard, they can validate again manually.
        """
        # First, check for IMEI validation products without serials (must raise error)
        self._check_imei_products_serials()
        
        # Second, validate IMEI numbers via API (must be done before allowing validation)
        self._validate_imei_via_api()
        
        # Then, check for non-IMEI products without serials (show wizard)
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

        # Call parent method
        return super(StockPicking, self).button_validate()

    def _check_imei_products_serials(self):
        """
        Check for IMEI validation products without serial numbers and raise error.
        This must be done BEFORE allowing validation, as IMEI serials must be entered manually.
        """
        precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        
        for picking in self:
            # Only check pickings that use create or existing lots
            if not (picking.picking_type_id.use_create_lots or picking.picking_type_id.use_existing_lots):
                continue

            # Get move lines that need to be checked
            move_lines = picking.move_line_ids.filtered(
                lambda ml: ml.state not in ('done', 'cancel')
            )

            # Collect products requiring IMEI validation without serials
            missing_imei_products = []
            
            for ml in move_lines:
                # Check if quantity is positive
                qty_done_float_compared = float_compare(
                    ml.quantity, 0, 
                    precision_rounding=ml.product_uom_id.rounding
                )
                
                if qty_done_float_compared <= 0:
                    continue

                # Skip if product doesn't require tracking
                if ml.product_id.tracking == 'none':
                    continue

                # Check if lot/serial is already provided
                if ml.lot_id or ml.lot_name:
                    continue

                # Check exclusions (inventory adjustments and scrap don't require IMEI)
                if ml.is_inventory or ml.move_id.scrap_id:
                    continue

                # Check if this product requires IMEI validation
                if self._should_validate_imei_for_product(ml.product_id):
                    missing_imei_products.append(ml.product_id.display_name)
                    _logger.warning(f'Product {ml.product_id.display_name} requires IMEI validation but no serial/lot number provided')

            # If any IMEI products are missing serials, raise error
            if missing_imei_products:
                products_list = "\n".join(f"- {product_name}" for product_name in missing_imei_products)
                raise UserError(
                    _(
                        "The following products require IMEI validation and must have serial/lot numbers entered manually:\n\n"
                        "%(products)s\n\n"
                        "Please enter the IMEI as the Lot/Serial Number for these products before validating.",
                        products=products_list,
                    )
                )

    def _validate_imei_via_api(self):
        """
        Validate IMEI numbers via API for all products requiring IMEI validation.
        This must be done BEFORE allowing picking validation.
        Raises error if any IMEI validation fails.
        """
        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        validation_required = IrConfigParameter.get_param(
            'quality_control_imei.validation_required',
            default='True'
        ) == 'True'
        
        # Skip if validation is not required
        if not validation_required:
            _logger.info('IMEI validation is disabled in settings')
            return
        
        precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        
        for picking in self:
            # Only check pickings that use create or existing lots
            if not (picking.picking_type_id.use_create_lots or picking.picking_type_id.use_existing_lots):
                continue

            # Get move lines that need to be checked
            move_lines = picking.move_line_ids.filtered(
                lambda ml: ml.state not in ('done', 'cancel')
            )

            # Validate IMEI for each line requiring it
            for ml in move_lines:
                # Check if quantity is positive
                qty_done_float_compared = float_compare(
                    ml.quantity, 0, 
                    precision_rounding=ml.product_uom_id.rounding
                )
                
                if qty_done_float_compared <= 0:
                    continue

                # Skip if product doesn't require tracking
                if ml.product_id.tracking == 'none':
                    continue

                # Skip if no lot_name (already checked in _check_imei_products_serials)
                if not ml.lot_name:
                    continue

                # Check exclusions (inventory adjustments and scrap don't require IMEI)
                if ml.is_inventory or ml.move_id.scrap_id:
                    continue

                # Check if this product requires IMEI validation
                if not self._should_validate_imei_for_product(ml.product_id):
                    continue

                # At this point, we have an IMEI product with a lot_name - validate it
                imei = ml.lot_name
                _logger.info(f'Validating IMEI "{imei}" for product {ml.product_id.display_name}')
                
                # Call API to validate IMEI
                validation_result = self._call_imei_validation_api(imei)
                
                if not validation_result.get('success', False):
                    raise UserError(_(
                        'IMEI validation failed for product "%(product)s":\n\n'
                        'IMEI: %(imei)s\n'
                        'Error: %(error)s\n\n'
                        'Please verify the IMEI number before validating the picking.',
                        product=ml.product_id.display_name,
                        imei=imei,
                        error=validation_result.get('message', 'Unknown error')
                    ))

                result = validation_result.get('result') or {}

                # Check if IMEI is actually valid
                if not result.get('imei', False):
                    raise UserError(_(
                        'IMEI is not valid for product "%(product)s":\n\n'
                        'IMEI: %(imei)s\n'
                        'Error: %(error)s\n\n'
                        'Cannot validate picking with invalid IMEI.',
                        product=ml.product_id.display_name,
                        imei=imei,
                        error=validation_result.get('message', 'IMEI validation failed')
                    ))

                # Post success message to picking
                imei_value = result.get('imei', 'N/A')
                brand_value = result.get('brand_name', 'N/A')
                model_value = result.get('model', 'N/A')
                
                message_body = Markup(
                    "<p><strong>%s</strong></p>"
                    "<ul>"
                    "<li><strong>%s:</strong> %s</li>"
                    "<li><strong>%s:</strong> %s</li>"
                    "<li><strong>%s:</strong> %s</li>"
                    "<li><strong>%s:</strong> %s</li>"
                    "</ul>"
                ) % (
                    _('IMEI Validation Successful'),
                    _('Product'), ml.product_id.display_name,
                    _('IMEI'), imei_value,
                    _('Brand'), brand_value,
                    _('Model'), model_value
                )
                
                picking.message_post(body=message_body)
                _logger.info(f'IMEI "{imei}" validated successfully for product {ml.product_id.display_name}')

    def _call_imei_validation_api(self, imei):
        """
        Call external API to validate IMEI number.
        Returns dict with validation result.
        """
        if not imei:
            return {
                'success': False,
                'valid': False,
                'message': 'IMEI is required',
                'status': 'error'
            }

        # Get API configuration from system parameters
        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        api_url = IrConfigParameter.get_param('quality_control_imei.api_url')
        if not api_url:
            raise UserError(_(
                'IMEI Validation API URL is not configured.\n'
                'Please configure it in Settings > Inventory > Quality Control IMEI.'
            ))

        api_key = IrConfigParameter.get_param('quality_control_imei.api_key')
        if not api_key:
            raise UserError(_(
                'IMEI Validation API Key is not configured.\n'
                'Please configure it in Settings > Inventory > Quality Control IMEI.'
            ))

        timeout_param = IrConfigParameter.get_param(
            'quality_control_imei.api_timeout',
            default='10'
        )
        timeout = int(timeout_param) if timeout_param else 10

        try:
            # Prepare API request
            headers = {
                'Content-Type': 'application/json',
            }

            payload = {
                'API_KEY': api_key,
                'imei': imei
            }

            _logger.info(f'Validating IMEI: {imei} via API: {api_url}')

            # Make API call
            response = requests.get(
                api_url,
                params=payload,
                headers=headers,
                timeout=timeout
            )

            # Parse response
            if response.ok:
                data = response.json()
                return {
                    'success': True,
                    'valid': data.get('valid', False),
                    'message': data.get('message', 'IMEI validated successfully'),
                    'status': 'valid' if data.get('valid', False) else 'invalid',
                    'result': data.get('result', {})
                }
            else:
                _logger.error(f'API validation failed with status {response.status_code}: {response.text}')
                return {
                    'success': False,
                    'valid': False,
                    'message': f'API returned status code {response.status_code}',
                    'status': 'error',
                    'raw_response': response.text
                }

        except requests.exceptions.Timeout:
            _logger.error(f'API timeout while validating IMEI: {imei}')
            return {
                'success': False,
                'valid': False,
                'message': 'API request timeout',
                'status': 'error'
            }
        except requests.exceptions.RequestException as e:
            _logger.error(f'API request error: {str(e)}')
            return {
                'success': False,
                'valid': False,
                'message': f'API request error: {str(e)}',
                'status': 'error'
            }
        except Exception as e:
            _logger.error(f'Unexpected error validating IMEI: {str(e)}')
            return {
                'success': False,
                'valid': False,
                'message': f'Unexpected error: {str(e)}',
                'status': 'error'
            }

    def _check_missing_lots(self):
        """
        Check for move lines that require lot/serial numbers but don't have them.
        This replicates the logic from stock.move.line._action_done() to prevent
        the error from being raised.
        
        Excludes products that require IMEI validation - those should be entered manually.
        """
        pickings_without_lots = self.browse()
        precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        for picking in self:
            # Only check pickings that use create or existing lots
            if not (picking.picking_type_id.use_create_lots or picking.picking_type_id.use_existing_lots):
                continue

            # Get move lines that need to be checked
            move_lines = picking.move_line_ids.filtered(
                lambda ml: ml.state not in ('done', 'cancel')
            )

            for ml in move_lines:
                # Check if quantity is positive
                qty_done_float_compared = float_compare(
                    ml.quantity, 0, 
                    precision_rounding=ml.product_uom_id.rounding
                )
                
                if qty_done_float_compared <= 0:
                    continue

                # Skip if product doesn't require tracking
                if ml.product_id.tracking == 'none':
                    continue

                # Check if lot/serial is already provided
                if ml.lot_id or ml.lot_name:
                    continue

                # EXCLUDE products that require IMEI validation
                # These should be entered manually, not auto-generated
                # Only exclude if categories are configured and product is in them
                if self._should_validate_imei_for_product(ml.product_id):
                    _logger.info(f'Excluding product {ml.product_id.display_name} from auto-serial generation (IMEI validation required)')
                    continue

                # Check exclusions (same logic as _exclude_requiring_lot)
                picking_type_id = ml.move_id.picking_type_id
                if ml.is_inventory or ml.move_id.scrap_id:
                    continue

                # If both checkboxes are disabled, allow without lot
                if picking_type_id and not picking_type_id.use_create_lots and not picking_type_id.use_existing_lots:
                    continue

                # If we reach here, this line requires a lot but doesn't have one
                pickings_without_lots |= picking
                break  # No need to check other lines in this picking

        return pickings_without_lots
