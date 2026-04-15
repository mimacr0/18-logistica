# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class RmaUnitStoreWizard(models.TransientModel):
    _name = 'rma.unit.store.wizard'
    _description = 'Store RMA units in a location'

    rma_unit_ids = fields.Many2many('rma.unit', string='RMA units', required=True)
    location_id = fields.Many2one(
        'stock.location',
        string='Storage location',
        required=True,
        domain="[('usage', '=', 'internal')]",
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_ids = self.env.context.get('active_ids')
        if active_ids and 'rma_unit_ids' in fields_list:
            res['rma_unit_ids'] = [(6, 0, active_ids)]
        return res

    def action_confirm(self):
        self.ensure_one()
        if not self.rma_unit_ids:
            raise UserError(_('No RMA units selected.'))
        self.rma_unit_ids.with_context(rma_transition_reason=_('Store')).write({
            'state': 'stored',
            'location_id': self.location_id.id,
        })
        return {'type': 'ir.actions.act_window_close'}
