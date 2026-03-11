# -*- coding: utf-8 -*-
from odoo import models, fields, api

class RmaRepairAddPartsWizard(models.TransientModel):
    _name = 'rma.repair.add.parts.wizard'
    _description = 'Wizard to add spare parts'

    repair_id = fields.Many2one('rma.repair', string='Repair', required=True)
    owner_id = fields.Many2one('res.partner', related='repair_id.owner_id')
    quant_ids = fields.Many2many(
        'stock.quant', 
        string='Spare Parts',
        domain="[('owner_id', '=', owner_id), ('quantity', '>', 0), ('product_id.is_spare_parts', '=', True), ('product_id.type', '!=', 'service')]"
    )

    def action_add_parts(self):
        self.ensure_one()
        if self.quant_ids:
            # We add to the current list of spare parts
            self.repair_id.write({
                'spare_part_ids': [(4, quant.id) for quant in self.quant_ids]
            })
        return {'type': 'ir.actions.act_window_close'}
