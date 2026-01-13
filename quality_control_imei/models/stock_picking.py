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
from odoo.tools.float_utils import float_compare
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _should_validate_imei_for_product(self, product):
        """
        Check if IMEI validation is required for this product based on configured categories.
        Returns True if product belongs to configured IMEI categories.
        """
        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        category_ids_str = IrConfigParameter.get_param('quality_control_imei.category_ids', default='')
        
        if not category_ids_str:
            return False
        
        configured_category_ids = [int(id_str) for id_str in category_ids_str.split(',') if id_str.strip()]
        if not configured_category_ids:
            return False
        
        # Get all parent categories of the product's category
        product_category = product.categ_id
        category_path = []
        current_category = product_category
        
        while current_category:
            category_path.append(current_category.id)
            current_category = current_category.parent_id
        
        # Check if any of the product's categories match configured ones
        for category_id in category_path:
            if category_id in configured_category_ids:
                return True
        
        # Check if product category is a child of any configured category
        configured_categories = self.env['product.category'].browse(configured_category_ids)
        for configured_cat in configured_categories:
            if product_category.id == configured_cat.id:
                return True
            if self._is_category_descendant(product_category, configured_cat):
                return True
        
        return False

    def _is_category_descendant(self, category, parent_category):
        """Check if category is a descendant of parent_category"""
        current = category.parent_id
        while current:
            if current.id == parent_category.id:
                return True
            current = current.parent_id
        return False

    def _should_exclude_from_auto_serial(self, product):
        """
        Override hook from stock_barcode_auto_serial.
        Exclude products that require IMEI validation from auto-serial generation.
        """
        # First check parent exclusions
        if super()._should_exclude_from_auto_serial(product):
            return True
        # Then check IMEI exclusion
        return self._should_validate_imei_for_product(product)

    def _pre_action_done_hook(self):
        """
        Override to add IMEI validation before the auto-serial wizard.
        1. Check IMEI products have serials (raise error if missing)
        2. Validate IMEI numbers via API
        3. Let parent handle auto-serial wizard
        """
        # First, check for IMEI validation products without serials (must raise error)
        self._check_imei_products_serials()
        
        # Second, validate IMEI numbers via API
        self._validate_imei_via_api()
        
        # Let parent (stock_barcode_auto_serial) handle auto-serial wizard
        return super(StockPicking, self)._pre_action_done_hook()

    def _check_imei_products_serials(self):
        """
        Check for IMEI validation products without serial numbers and raise error.
        IMEI serials must be entered manually.
        """
        for picking in self:
            if not (picking.picking_type_id.use_create_lots or picking.picking_type_id.use_existing_lots):
                continue

            move_lines = picking.move_line_ids.filtered(
                lambda ml: ml.state not in ('done', 'cancel')
            )

            missing_imei_products = []
            
            for ml in move_lines:
                qty_done = float_compare(ml.quantity, 0, precision_rounding=ml.product_uom_id.rounding)
                if qty_done <= 0:
                    continue

                if ml.product_id.tracking == 'none':
                    continue

                if ml.lot_id or ml.lot_name:
                    continue

                if ml.is_inventory or ml.move_id.scrap_id:
                    continue

                if self._should_validate_imei_for_product(ml.product_id):
                    missing_imei_products.append(ml.product_id.display_name)

            if missing_imei_products:
                products_list = "\n".join(f"- {name}" for name in missing_imei_products)
                raise UserError(_(
                    "The following products require IMEI validation and must have serial/lot numbers entered manually:\n\n"
                    "%(products)s\n\n"
                    "Please enter the IMEI as the Lot/Serial Number for these products before validating.",
                    products=products_list,
                ))

    def _validate_imei_via_api(self):
        """
        Validate IMEI numbers via API for all products requiring IMEI validation.
        """
        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        validation_required = IrConfigParameter.get_param(
            'quality_control_imei.validation_required', default='True'
        ) == 'True'
        
        if not validation_required:
            return
        
        for picking in self:
            if not (picking.picking_type_id.use_create_lots or picking.picking_type_id.use_existing_lots):
                continue

            move_lines = picking.move_line_ids.filtered(
                lambda ml: ml.state not in ('done', 'cancel')
            )

            for ml in move_lines:
                qty_done = float_compare(ml.quantity, 0, precision_rounding=ml.product_uom_id.rounding)
                if qty_done <= 0:
                    continue

                if ml.product_id.tracking == 'none':
                    continue

                if not ml.lot_name:
                    continue

                if ml.is_inventory or ml.move_id.scrap_id:
                    continue

                if not self._should_validate_imei_for_product(ml.product_id):
                    continue

                # Validate IMEI via API
                imei = ml.lot_name
                validation_result = self._call_imei_validation_api(imei)
                
                if not validation_result.get('success', False):
                    raise UserError(_(
                        'IMEI validation failed for product "%(product)s":\n\n'
                        'IMEI: %(imei)s\n'
                        'Error: %(error)s',
                        product=ml.product_id.display_name,
                        imei=imei,
                        error=validation_result.get('message', 'Unknown error')
                    ))

                result = validation_result.get('result') or {}
                if not result.get('imei', False):
                    raise UserError(_(
                        'IMEI is not valid for product "%(product)s":\n\n'
                        'IMEI: %(imei)s',
                        product=ml.product_id.display_name,
                        imei=imei,
                    ))

                # Post success message
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
                    _('IMEI'), result.get('imei', 'N/A'),
                    _('Brand'), result.get('brand_name', 'N/A'),
                    _('Model'), result.get('model', 'N/A')
                )
                picking.message_post(body=message_body)

    def _call_imei_validation_api(self, imei):
        """Call external API to validate IMEI number."""
        if not imei:
            return {'success': False, 'message': 'IMEI is required'}

        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        api_url = IrConfigParameter.get_param('quality_control_imei.api_url')
        if not api_url:
            raise UserError(_('IMEI Validation API URL is not configured.'))

        api_key = IrConfigParameter.get_param('quality_control_imei.api_key')
        if not api_key:
            raise UserError(_('IMEI Validation API Key is not configured.'))

        timeout = int(IrConfigParameter.get_param('quality_control_imei.api_timeout', default='10'))

        try:
            headers = {'Content-Type': 'application/json'}
            payload = {'API_KEY': api_key, 'imei': imei}

            response = requests.get(api_url, params=payload, headers=headers, timeout=timeout)

            if response.ok:
                data = response.json()
                return {
                    'success': True,
                    'valid': data.get('valid', False),
                    'message': data.get('message', 'IMEI validated successfully'),
                    'result': data.get('result', {})
                }
            else:
                return {
                    'success': False,
                    'message': f'API returned status code {response.status_code}'
                }

        except requests.exceptions.Timeout:
            return {'success': False, 'message': 'API request timeout'}
        except requests.exceptions.RequestException as e:
            return {'success': False, 'message': f'API request error: {str(e)}'}
        except Exception as e:
            return {'success': False, 'message': f'Unexpected error: {str(e)}'}
