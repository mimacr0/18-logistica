from odoo import models, fields, api, _
from odoo.exceptions import UserError


class RmaRepairHarvestWizard(models.TransientModel):
    _name = 'rma.repair.harvest.wizard'
    _description = 'Harvest spare parts from an RMA unit'

    repair_unit_id = fields.Many2one(
        'rma.unit',
        string='Unit under repair (do not dismantle)',
        readonly=True,
        help='Filled when opening the wizard from a repair order (shortcut only; not stored on the harvest).',
    )
    unit_id = fields.Many2one(
        'rma.unit',
        string='Unit to dismantle',
        required=True,
        domain="[('id', '!=', repair_unit_id)]",
        help='RMA unit to convert into spare parts.',
    )
    owner_id = fields.Many2one(
        'res.partner',
        string='Owner',
        compute='_compute_owner_id',
    )
    location_id = fields.Many2one(
        'stock.location',
        string='Target Location',
        required=True,
        default=lambda self: self._default_harvest_location_id(),
    )
    line_ids = fields.One2many('rma.repair.harvest.wizard.line', 'wizard_id', string='Parts to Harvest')

    @api.model
    def _default_harvest_location_id(self):
        loc = self.env.ref(
            'rma_inventory.stock_location_rma_repair_department_warehouse',
            raise_if_not_found=False,
        )
        return loc.id if loc else False

    @api.depends('unit_id.owner_id')
    def _compute_owner_id(self):
        for wiz in self:
            wiz.owner_id = wiz.unit_id.owner_id if wiz.unit_id else False

    @api.model
    def _prepare_harvest_line_commands(self, unit):
        """Build (0, 0, vals) commands from product.template components_ids."""
        vals_list = self.env['rma.harvest.operation']._prepare_line_vals_from_unit(unit)
        return [(0, 0, v) for v in vals_list]

    @api.onchange('unit_id')
    def _onchange_unit_id(self):
        if self.unit_id:
            self.line_ids = [(5, 0, 0)] + self._prepare_harvest_line_commands(self.unit_id)
        else:
            self.line_ids = [(5, 0, 0)]

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        ruid = self._context.get('default_repair_unit_id')
        if ruid:
            res['repair_unit_id'] = ruid
        if 'location_id' in fields_list:
            ctx_loc = self._context.get('default_location_id')
            if ctx_loc:
                res.setdefault('location_id', ctx_loc)
            else:
                res.setdefault('location_id', self._default_harvest_location_id())
        return res

    def action_harvest(self):
        self.ensure_one()
        if not self.line_ids:
            return {'type': 'ir.actions.act_window_close'}

        if not self.location_id:
            raise UserError(_("Please select a target location for the harvested spare parts."))

        if self.repair_unit_id and self.unit_id == self.repair_unit_id:
            raise UserError(
                _('You cannot dismantle the unit under repair. Choose another RMA unit or use Add Spare Parts.')
            )

        operation = self.env['rma.harvest.operation'].create({
            'rma_unit_id': self.unit_id.id,
            'location_id': self.location_id.id,
            'line_ids': [
                (0, 0, {'product_id': line.product_id.id, 'quantity': line.quantity})
                for line in self.line_ids
            ],
        })

        harvest_log = []
        for line in self.line_ids:
            harvest_log.append(f"- {line.quantity}x {line.product_id.display_name}")

        ref = operation.name
        log_text = "Harvest operation %s — %s:\n%s\n" % (
            ref,
            fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "\n".join(harvest_log),
        )

        existing_notes = self.unit_id.harvest_notes or ""
        new_notes = existing_notes + "\n" + log_text if existing_notes else log_text

        self.unit_id.with_context(rma_transition_reason=_('Harvest for spare parts')).write({
            'state': 'stored',
            'location_id': self.location_id.id,
            'condition': 'converted_to_spare_parts',
            'harvest_notes': new_notes,
        })

        owner = self.unit_id.owner_id
        for line in self.line_ids:
            quant = self.env['stock.quant'].create({
                'product_id': line.product_id.id,
                'location_id': self.location_id.id,
                'owner_id': owner.id,
                'inventory_quantity': line.quantity,
            })
            quant.action_apply_inventory()

        return {'type': 'ir.actions.act_window_close'}


class RmaRepairHarvestWizardLine(models.TransientModel):
    _name = 'rma.repair.harvest.wizard.line'
    _description = 'Harvest Wizard Line'

    wizard_id = fields.Many2one('rma.repair.harvest.wizard', string='Wizard')
    product_id = fields.Many2one(
        'product.product',
        string='Part product',
        domain="[('product_tmpl_id.is_spare_parts', '=', True), ('type', '!=', 'service')]",
        required=True,
    )
    quantity = fields.Float(string='Quantity', default=1.0, required=True, digits='Product Unit of Measure')
