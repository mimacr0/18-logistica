# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class RmaUnitMoveDeskWizard(models.TransientModel):
    _name = 'rma.unit.move.desk.wizard'
    _description = 'Move RMA units between locations (desk)'

    location_dest_id = fields.Many2one(
        'stock.location',
        string='Default destination',
        domain="[('usage', '=', 'internal')]",
        help='Fills “To location” on all lines; you can change each line before confirming.',
    )
    line_ids = fields.One2many(
        'rma.unit.move.desk.wizard.line',
        'wizard_id',
        string='Units',
        required=True,
    )

    @api.onchange('location_dest_id')
    def _onchange_location_dest_id(self):
        if self.location_dest_id:
            for line in self.line_ids:
                line.to_location_id = self.location_dest_id

    def action_confirm(self):
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_('Add at least one RMA unit line.'))
        for line in self.line_ids:
            if not line.to_location_id:
                raise UserError(
                    _('Each line must have a destination location (unit %s).') % (line.rma_unit_id.display_name,)
                )
            old_loc = line.rma_unit_id.location_id.id if line.rma_unit_id.location_id else False
            if line.to_location_id.id == old_loc:
                continue
            line.rma_unit_id.with_context(rma_transition_reason=_('Move desk')).write({
                'location_id': line.to_location_id.id,
            })
        return {'type': 'ir.actions.act_window_close'}


class RmaUnitMoveDeskWizardLine(models.TransientModel):
    _name = 'rma.unit.move.desk.wizard.line'
    _description = 'RMA unit move desk line'

    wizard_id = fields.Many2one(
        'rma.unit.move.desk.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade',
    )
    rma_unit_id = fields.Many2one(
        'rma.unit',
        string='RMA unit',
        required=True,
        ondelete='cascade',
    )
    from_location_id = fields.Many2one(
        related='rma_unit_id.location_id',
        string='From location',
        readonly=True,
    )
    to_location_id = fields.Many2one(
        'stock.location',
        string='To location',
        domain="[('usage', '=', 'internal')]",
        required=True,
    )
