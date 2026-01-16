# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2025 DaFe Solutions
#
##############################################################################

from odoo import models, fields, api, _


class QualityAlertCancelWizard(models.TransientModel):
    _name = 'quality.alert.cancel.wizard'
    _description = 'Quality Alert Cancel Wizard'

    alert_id = fields.Many2one('quality.alert', string='Alert', required=True)
    reason = fields.Text(string='Cancellation Reason', required=True)
    has_done_pickings = fields.Boolean(string='Has Done Pickings', compute='_compute_has_done_pickings')
    has_repairs = fields.Boolean(string='Has Repairs', compute='_compute_has_repairs')

    @api.depends('alert_id')
    def _compute_has_done_pickings(self):
        for wizard in self:
            wizard.has_done_pickings = bool(wizard.alert_id.picking_ids.filtered(lambda p: p.state == 'done'))

    @api.depends('alert_id')
    def _compute_has_repairs(self):
        for wizard in self:
            wizard.has_repairs = bool(wizard.alert_id.repair_order_ids)

    def action_confirm_cancel(self):
        """Confirms the cancellation with the provided reason."""
        self.ensure_one()
        self.alert_id._do_cancel(reason=self.reason)
        return {'type': 'ir.actions.act_window_close'}
