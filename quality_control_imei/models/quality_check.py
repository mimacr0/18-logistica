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
            # Get IMEI from lot name
            imei = line.lot_name

            if not imei and validation_required:
                raise UserError(_(
                    'No IMEI found in lot/serial number for this quality check.\n'
                    'Cannot pass quality check without IMEI.'
                ))

            # If IMEI is present and validation is required, validate it before passing
            if imei and validation_required:
                validation_result = self._validate_imei_via_api(imei)
                if not validation_result.get('success', False):
                    raise UserError(_(
                        'IMEI validation failed: %s\nPlease verify the IMEI before passing the quality check.'
                    ) % validation_result.get('message', 'Unknown error'))

                result = validation_result.get('result') or {}

                # Check if IMEI is actually valid
                if not result.get('imei', False):
                    raise UserError(_(
                        'IMEI is not valid: %s\nCannot pass quality check with invalid IMEI.'
                    ) % validation_result.get('message', 'IMEI validation failed'))

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
                    "</ul>"
                ) % (
                    _('IMEI Validation Successful'),
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
