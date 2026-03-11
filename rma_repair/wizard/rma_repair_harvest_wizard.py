from odoo import models, fields, api, _
from odoo.exceptions import UserError

class RmaRepairHarvestWizard(models.TransientModel):
    _name = 'rma.repair.harvest.wizard'
    _description = 'Harvest Spare Parts from Unit'

    repair_id = fields.Many2one('rma.repair', string='Repair', required=True)
    unit_id = fields.Many2one('rma.unit', string='Unit to Harvest', required=True)
    owner_id = fields.Many2one('res.partner', related='repair_id.owner_id')
    location_id = fields.Many2one('stock.location', string='Target Location', required=True)
    line_ids = fields.One2many('rma.repair.harvest.wizard.line', 'wizard_id', string='Parts to Harvest')

    @api.onchange('unit_id')
    def _onchange_unit_id(self):
        if self.unit_id:
            self.location_id = self.unit_id.location_id

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if self._context.get('active_id'):
            repair = self.env['rma.repair'].browse(self._context.get('active_id'))
            res.update({
                'repair_id': repair.id,
                'unit_id': repair.unit_id.id,
                'location_id': repair.unit_id.location_id.id,
            })
        return res

    def action_harvest(self):
        self.ensure_one()
        if not self.line_ids:
            return {'type': 'ir.actions.act_window_close'}

        if not self.location_id:
            raise UserError(_("Please select a target location. The original unit does not have a location set."))

        # 1. Update unit state and condition
        # Build the note for harvested parts first
        harvest_log = []
        for line in self.line_ids:
            harvest_log.append(f"- {line.quantity}x {line.product_id.display_name}")
        
        log_text = "Harvested Parts on {}:\n{}\n".format(
            fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "\n".join(harvest_log)
        )
        
        existing_notes = self.unit_id.harvest_notes or ""
        new_notes = existing_notes + "\n" + log_text if existing_notes else log_text

        self.unit_id.write({
            'state': 'use_for_spare_parts',
            'condition': 'converted_to_spare_parts',
            'harvest_notes': new_notes
        })

        # 2. Create spare parts (stock.quant)
        new_quant_ids = []
        for line in self.line_ids:
            # We look for or create a quant in the target location
            quant = self.env['stock.quant'].create({
                'product_id': line.product_id.id,
                'location_id': self.location_id.id,
                'owner_id': self.owner_id.id,
                'inventory_quantity': line.quantity,
            })
            # Apply inventory to make it "real" stock
            quant.action_apply_inventory()
            new_quant_ids.append(quant.id)

        return {'type': 'ir.actions.act_window_close'}

class RmaRepairHarvestWizardLine(models.TransientModel):
    _name = 'rma.repair.harvest.wizard.line'
    _description = 'Harvest Wizard Line'

    wizard_id = fields.Many2one('rma.repair.harvest.wizard', string='Wizard')
    product_id = fields.Many2one('product.product', string='Spare Part Product', 
                                domain="[('is_spare_parts', '=', True)]", required=True)
    quantity = fields.Float(string='Quantity', default=1.0, required=True)
