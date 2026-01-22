# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from markupsafe import Markup

from odoo import models, _

_logger = logging.getLogger(__name__)


class QualityCheckWizard(models.TransientModel):
    _inherit = 'quality.check.wizard'

    def confirm_fail(self):
        _logger.info("QC confirm_fail start | wizard_ids=%s", self.ids)
        action = super().confirm_fail()
        _logger.info("QC confirm_fail after super | action=%s", action)
        self._create_quality_alert_for_fail()
        self._notify_account_partner_failure()
        self._notify_account_partner_system_notification()
        _logger.info("QC confirm_fail end | wizard_ids=%s", self.ids)
        return action

    def _create_quality_alert_for_fail(self):
        for wizard in self:
            check = wizard.current_check_id
            if not check:
                _logger.info("QC alert skip | no check | wizard_id=%s", wizard.id)
                continue

            account_partner = check.picking_id.account_partner_id if check.picking_id else False
            if not account_partner and check.picking_id and check.picking_id.partner_id and \
                    'account_id' in check.picking_id.partner_id._fields:
                account_partner = check.picking_id.partner_id.account_id

            default_stage = self.env.ref(
                'stock_reception.quality_alert_stage_qc_failed',
                raise_if_not_found=False,
            )
            description = '<br/>'.join(filter(None, [wizard.note, wizard.additional_note])) or False
            alert_title = _(
                "%(check)s failed - %(account)s",
                check=check.name or _('Quality Check'),
                account=account_partner.name if account_partner else _('No account'),
            )
            alert_vals = {
                'name': alert_title,
                'title': alert_title,
                'description': description,
                'check_id': check.id,
                'picking_id': check.picking_id.id if check.picking_id else False,
                'product_id': check.product_id.id if check.product_id else False,
                'product_tmpl_id': check.product_id.product_tmpl_id.id if check.product_id else False,
                'lot_id': check.lot_id.id if check.lot_id else wizard.lot_line_id.id if wizard.lot_line_id else False,
                'user_id': check.user_id.id if check.user_id else self.env.user.id,
                'team_id': check.team_id.id if check.team_id else False,
                'company_id': check.company_id.id if check.company_id else self.env.company.id,
                'partner_id': account_partner.partner_id.id if account_partner and account_partner.partner_id else False,
                'account_partner_id': account_partner.id if account_partner else False,
                'stage_id': default_stage.id if default_stage else False,
            }
            print(alert_vals['stage_id'])
            print(default_stage)
            print(default_stage.id)
            print(alert_vals['stage_id'] == default_stage.id)
            print(alert_vals['stage_id'] == default_stage.id)
            alert_vals = {key: val for key, val in alert_vals.items() if val}
            alert = self.env['quality.alert'].create(alert_vals)
            _logger.info(
                "QC alert created | wizard_id=%s check_id=%s alert_id=%s",
                wizard.id,
                check.id,
                alert.id,
            )

    def _notify_account_partner_failure(self):
        for wizard in self:
            _logger.info(
                "QC notify start | wizard_id=%s check_id=%s",
                wizard.id,
                wizard.current_check_id.id,
            )
            picking = wizard.current_check_id.picking_id
            if not picking:
                _logger.info("QC notify skip | no picking | wizard_id=%s", wizard.id)
                continue

            account_partner = picking.account_partner_id
            if not account_partner and picking.partner_id and 'account_id' in picking.partner_id._fields:
                account_partner = picking.partner_id.account_id

            if not account_partner or not account_partner.partner_id:
                _logger.info(
                    "QC notify skip | no account partner | wizard_id=%s picking=%s",
                    wizard.id,
                    picking.name,
                )
                continue

            partner = account_partner.partner_id
            failure_location = wizard.failure_location_id.display_name if wizard.failure_location_id else _('No location')
            product_name = wizard.product_id.display_name if wizard.product_id else _('Unknown product')
            lot_name = wizard.lot_name or _('No lot')
            _logger.info(
                "QC notify target | wizard_id=%s picking=%s partner=%s",
                wizard.id,
                picking.name,
                partner.display_name,
            )

            body = Markup(_(
                "Quality check failed on picking %(picking)s.<br/>"
                "Product: %(product)s<br/>"
                "Lot/Serial: %(lot)s<br/>"
                "Failed qty: %(qty)s<br/>"
                "Failure location: %(location)s"
            )) % {
                'picking': picking.name or '',
                'product': product_name,
                'lot': lot_name,
                'qty': wizard.qty_failed or wizard.qty_line or 0,
                'location': failure_location,
            }

            partner.message_post(
                body=Markup(body),
                subject=_('Quality check failed'),
                message_type='notification',
                subtype_xmlid='mail.mt_note',
            )
            _logger.info(
                "QC notify sent | wizard_id=%s picking=%s partner=%s",
                wizard.id,
                picking.name,
                partner.display_name,
            )

    def _notify_account_partner_system_notification(self):
        if 'portal.user.notification' not in self.env:
            _logger.info("QC system notify skip | portal.user.notification not installed")
            return

        PortalNotification = self.env['portal.user.notification'].sudo()
        for wizard in self:
            picking = wizard.current_check_id.picking_id
            if not picking:
                _logger.info("QC system notify skip | no picking | wizard_id=%s", wizard.id)
                continue

            account_partner = picking.account_partner_id
            if not account_partner and picking.partner_id and 'account_id' in picking.partner_id._fields:
                account_partner = picking.partner_id.account_id

            if not account_partner or not account_partner.partner_id:
                _logger.info(
                    "QC system notify skip | no account partner | wizard_id=%s picking=%s",
                    wizard.id,
                    picking.name,
                )
                continue

            partner = account_partner.partner_id
            users = partner.user_ids | partner.portal_user_ids.mapped('user_ids')
            users = users.filtered(lambda u: u.active)
            if not users:
                _logger.info(
                    "QC system notify skip | no users | wizard_id=%s partner=%s",
                    wizard.id,
                    partner.display_name,
                )
                continue

            product_name = wizard.product_id.display_name if wizard.product_id else _('Unknown product')
            lot_name = wizard.lot_name or _('No lot')
            note = wizard.additional_note or _('No note')
            move_line = wizard.current_check_id.move_line_id if wizard.current_check_id else False
            package = False
            if move_line:
                package = move_line.result_package_id or move_line.package_id or move_line.origin_package_id
            if not package and picking:
                package = (
                    picking.move_line_ids.mapped('result_package_id')
                    or picking.move_line_ids.mapped('package_id')
                    or picking.move_line_ids.mapped('origin_package_id')
                )[:1]
            package_name = package.name if package else _('No package')
            message = _(
                "QC failed on %(package)s | %(product)s | Lot: %(lot)s | Qty: %(qty)s | Note: %(note)s"
            ) % {
                'package': package_name,
                'product': product_name,
                'lot': lot_name,
                'qty': wizard.qty_failed or wizard.qty_line or 0,
                'note': note,
            }

            for user in users:
                PortalNotification.create_notification(
                    user.id,
                    _('Quality check failed'),
                    message,
                    icon='exclamation-triangle',
                )
                _logger.info(
                    "QC system notify sent | wizard_id=%s user=%s",
                    wizard.id,
                    user.login,
                )
