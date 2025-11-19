# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2025 DaFe Solutions
#
##############################################################################

import requests
import logging
from markupsafe import Markup
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class QualityCheckImei(models.Model):
    _inherit = 'quality.check'

    # IMEI is retrieved from lot_name field
    # No inheritance of stock.lot - validation uses existing lot records

    def _should_validate_imei_for_product(self, product):
        """
        Check if IMEI validation is required for this product based on configured categories
        Returns True if:
        - No categories are configured (validate all products)
        - Product belongs to one of the configured categories or their subcategories
        """
        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        category_ids_str = IrConfigParameter.get_param('quality_control_imei.category_ids', default='')
        
        # If no categories configured, validate all products
        if not category_ids_str:
            return True
        
        # Parse configured category IDs
        configured_category_ids = [int(id_str) for id_str in category_ids_str.split(',') if id_str.strip()]
        if not configured_category_ids:
            return True
        
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

    def do_pass(self):
        """
        Override do_pass to validate IMEI before passing the quality check
        IMEI is retrieved from lot name
        """
        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        validation_required = IrConfigParameter.get_param(
            'quality_control_imei.validation_required',
            default='True'
        ) == 'True'

        for line in self.picking_id.move_ids.move_line_ids:
            product = line.product_id
            
            # Check if this product requires IMEI validation based on configured categories
            should_validate = self._should_validate_imei_for_product(product)
            
            # Skip validation if product is not in configured categories
            if not should_validate:
                continue
            
            # Get IMEI from lot name
            imei = line.lot_name

            if not imei and validation_required:
                raise UserError(_(
                    'No IMEI found in lot/serial number for product "%s".\n'
                    'Cannot pass quality check without IMEI for products in configured categories.'
                ) % product.display_name)

            # If IMEI is present and validation is required, validate it before passing
            if imei and validation_required:
                validation_result = self._validate_imei_via_api(imei)
                if not validation_result.get('success', False):
                    raise UserError(_(
                        'IMEI validation failed for product "%s": %s\n'
                        'Please verify the IMEI before passing the quality check.'
                    ) % (product.display_name, validation_result.get('message', 'Unknown error')))

                result = validation_result.get('result') or {}

                # Check if IMEI is actually valid
                if not result.get('imei', False):
                    raise UserError(_(
                        'IMEI is not valid for product "%s": %s\n'
                        'Cannot pass quality check with invalid IMEI.'
                    ) % (product.display_name, validation_result.get('message', 'IMEI validation failed')))

                # Post formatted message to picking
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
                    _('Product'), product.display_name,
                    _('IMEI'), imei_value,
                    _('Brand'), brand_value,
                    _('Model'), model_value
                )
                
                self.picking_id.message_post(body=message_body)

        # Call parent method
        return super(QualityCheckImei, self).do_pass()

    @api.model
    def call_api_validate_imei(self, imei):
        """
        API method to validate IMEI externally
        Can be called from RPC or other modules

        :param imei: IMEI number to validate
        :param api_url: Optional API URL (if not provided, uses from settings)
        :param api_key: Optional API key (if not provided, uses from settings)
        :param timeout: Optional timeout in seconds (if not provided, uses from settings)
        :return: Dictionary with validation result
        """
        if not imei:
            return {
                'success': False,
                'valid': False,
                'message': 'IMEI is required',
                'status': 'error'
            }

        # Get API configuration from system parameters if not provided
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

    def _validate_imei_via_api(self, imei):
        """
        Internal method to validate IMEI via API
        Validates lot name against API without storing status on stock.lot
        """
        self.ensure_one()

        if not imei:
            return {
                'success': True,
                'message': 'No IMEI to validate'
            }

        # Call API validation
        result = self.call_api_validate_imei(imei)

        _logger.info(f'IMEI validation result for {imei}: {result.get("status", "unknown")}')

        return result

    def action_validate_imei(self):
        """
        Manual action to validate IMEI from lot name
        Can be called from button in UI
        """
        self.ensure_one()

        imei = self._get_imei_from_lot()
        if not imei:
            raise UserError(_('No lot/serial number found for this quality check.'))

        result = self._validate_imei_via_api(imei)

        if result.get('success') and result.get('valid'):
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('IMEI %s is valid: %s') % (imei, result.get('message', '')),
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Validation Failed'),
                    'message': _('IMEI %s validation failed: %s') % (imei, result.get('message', '')),
                    'type': 'warning',
                    'sticky': True,
                }
            }
