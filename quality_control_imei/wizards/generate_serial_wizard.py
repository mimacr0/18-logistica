# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2025 DaFe Solutions
#
##############################################################################

from odoo import models, fields, _


class GenerateSerialWizard(models.TransientModel):
    _name = 'generate.serial.wizard'
    _description = 'Generate Serial Numbers Wizard'

    picking_id = fields.Many2one('stock.picking', string='Picking', required=True, readonly=True)
    message = fields.Html(string='Message', readonly=True, default=lambda self: _(
        '<p>Some products require Lot/Serial numbers but none have been provided.</p>'
        '<p>Do you want to generate automated serial numbers for these products?</p>'
    ))

    def action_generate_serials(self):
        """Generate automated serial numbers for move lines without lots"""
        self.ensure_one()
        
        precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        pickings_using_lots = self.picking_id.filtered(
            lambda p: p.picking_type_id.use_create_lots or p.picking_type_id.use_existing_lots
        )
        
        if pickings_using_lots:
            lines_to_check = pickings_using_lots._get_lot_move_lines_for_sanity_check(set())
            for line in lines_to_check:
                if not line.lot_name and not line.lot_id:
                    # Generate automated serial number
                    sequence = self.env['ir.sequence'].next_by_code('stock.lot.serial') or _('New')
                    line.lot_name = f"{line.product_id.default_code or line.product_id.name}/{sequence}"
        
        # Call button_validate with skip_sanity_check to avoid infinite loop
        return self.picking_id.with_context(skip_sanity_check=True).button_validate()

    def action_cancel(self):
        """Cancel and return to picking"""
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}
