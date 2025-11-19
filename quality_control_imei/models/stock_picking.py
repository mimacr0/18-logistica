# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2025 DaFe Solutions
#
##############################################################################

import logging
from odoo import models, _
from odoo.tools.float_utils import float_is_zero
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        """
        Override button_validate
        """

        pickings_without_lots = self.browse()
        precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        if not self.env.context.get('skip_sanity_check', False):
            no_quantities_done_ids = set()
            for picking in self:
                has_pick = any(move.picked and move.state not in ('done', 'cancel') for move in picking.move_ids)
                if all(float_is_zero(move.quantity, precision_digits=precision_digits) for move in picking.move_ids.filtered(lambda m: m.state not in ('done', 'cancel') and (not has_pick or m.picked))):
                    pickings_without_quantities |= picking

            pickings_using_lots = self.filtered(lambda p: p.picking_type_id.use_create_lots or p.picking_type_id.use_existing_lots)
            if pickings_using_lots:
                lines_to_check = pickings_using_lots._get_lot_move_lines_for_sanity_check(no_quantities_done_ids)
                for line in lines_to_check:
                    if not line.lot_name and not line.lot_id:
                        pickings_without_lots |= line.picking_id

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
