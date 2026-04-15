# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class RmaRepair(models.Model):
    _name = 'rma.repair'
    _description = 'RMA Repair'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Repair Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    unit_id = fields.Many2one('rma.unit', string='Unit', required=True, tracking=True)
    unit_condition = fields.Selection(related='unit_id.condition', readonly=False, store=True, tracking=True)
    product_id = fields.Many2one('product.product', string='Product', related='unit_id.product_id', store=True)
    account_id = fields.Many2one('account.partner', string='Account', related='unit_id.owner_id.account_id', store=True)
    owner_id = fields.Many2one('res.partner', related='unit_id.owner_id', string='Owner', store=True)

    technician_id = fields.Many2one('res.users', string='Technician', default=lambda self: self.env.user, tracking=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'In Progress'),
        ('done', 'Repaired'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    type_id = fields.Many2one('rma.repair.ticket.type', string='Type', tracking=True)
    category_ids = fields.Many2many(
        'rma.repair.ticket.category',
        'rma_repair_ticket_category_rel',
        'repair_id',
        'category_id',
        string='Categories',
    )
    tag_ids = fields.Many2many(
        'rma.repair.ticket.tag',
        'rma_repair_ticket_tag_rel',
        'repair_id',
        'tag_id',
        string='Tags',
    )

    operation_ids = fields.One2many('repair.operation.line', 'repair_id', string='Operations')
    spare_part_ids = fields.Many2many(
        'stock.quant',
        'rma_repair_stock_quant_rel',
        'repair_id',
        'quant_id',
        string='Spare Parts',
        domain="[('owner_id', '=', owner_id), ('quantity', '>', 0), ('product_id.is_spare_parts', '=', True), ('product_id.type', '!=', 'service')]"
    )

    diagnostic_notes = fields.Html(string='Diagnostic Notes')
    result_notes = fields.Html(string='Result Notes')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('rma.repair.sequence') or _('New')
        return super().create(vals_list)

    def action_confirm_repair(self):
        self.write({'state': 'confirmed'})
        if self.unit_id:
            vals = {'state': 'repair'}
            loc = self.env.ref('rma_inventory.stock_location_rma_repair', raise_if_not_found=False)
            if loc:
                vals['location_id'] = loc.id
            self.unit_id.with_context(rma_transition_reason=_('Repair order confirmed')).write(vals)

    def action_draft(self):
        self.write({'state': 'draft'})
        if self.unit_id and self.unit_id.state == 'repair':
            self.unit_id.with_context(rma_transition_reason=_('Repair reset to draft')).write({'state': 'review'})

    def action_done_repair(self):
        self.write({'state': 'done'})
        if self.unit_id:
            self.unit_id.with_context(rma_transition_reason=_('Repair finished')).write({'state': 'stored'})

    def action_open_add_parts_wizard(self):
        self.ensure_one()
        return {
            'name': _('Add Spare Parts'),
            'type': 'ir.actions.act_window',
            'res_model': 'rma.repair.add.parts.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_repair_id': self.id,
            }
        }

    def action_open_harvest_wizard(self):
        """Shortcut to the harvest wizard (no link to this repair in the database)."""
        self.ensure_one()
        ctx = {}
        if self.unit_id:
            ctx['default_repair_unit_id'] = self.unit_id.id
        return {
            'name': _('Harvest spare parts'),
            'type': 'ir.actions.act_window',
            'res_model': 'rma.repair.harvest.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': ctx,
        }
