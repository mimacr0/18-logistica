##############################################################################
#
# Copyright 2025 DaFe Solutions
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from .choices import MAINTENANCE_TYPE, LIFECYCLE_STATE


class QualityAlert(models.Model):
    _inherit = 'quality.alert'

    repair_order_ids = fields.One2many(comodel_name='repair.order', inverse_name='repair_alert_id', string='Órdenes de reparación vinculadas')
    account_partner_id = fields.Many2one(string='Owner Account', comodel_name='account.partner')
    maintenance_type = fields.Selection(MAINTENANCE_TYPE, string='Maintenance Type')
    quantity = fields.Integer(string='Quantity')
    stock_picking_count = fields.Integer(compute='_compute_stock_picking_count')
    check_ids = fields.Many2one('quality.check', string='Quality Checks')
    picking_ids = fields.Many2many('stock.picking', 'quality_alert_picking_rel', string='Pickings', check_company=True)
    schedule_date = fields.Date(string="Schedule Date")

    @api.depends('picking_ids')
    def _compute_picking_id(self):
        for record in self:
            record.picking_id = record.picking_ids[:1] if record.picking_ids else False

    def _compute_stock_picking_count(self):
        for picking in self:
            picking.stock_picking_count = len(self.picking_id)

    @api.onchange('account_partner_id')
    def _set_partner_and_owner(self):
        for sale in self:
            if sale.account_partner_id and sale.account_partner_id.partner_id:
                sale.partner_id = sale.account_partner_id.partner_id
            else:
                sale.partner_id = False

    def action_create_move_to_repair(self):
        self.ensure_one()
        if self.quantity <= 0:
            raise ValidationError(_('Quantity must be greater than 0. Please check the value.'))            
        
        picking_type = self.env.ref('repair_module.stock_picking_type_move_to_repair')

        picking = self.env['stock.picking'].create({
            'account_partner_id': self.account_partner_id.id,
            'partner_id': self.account_partner_id.partner_id.id,
            'origin': self.name,
            'picking_type_id': picking_type.id,
            'location_id': self.lot_id.location_id.id if self.lot_id.location_id else False,
            'location_dest_id': picking_type.default_location_dest_id.id,
            'quality_alert_ids': [(6, 0, [self.id])],
            'maintenance_type': self.maintenance_type,
        })

        move = self.env['stock.move'].create({
            'name': self.product_id.display_name,
            'product_id': self.product_id.id,
            'product_uom_qty': self.quantity,
            'product_uom': self.product_id.uom_id.id,
            'picking_id': picking.id,
            'location_id': self.lot_id.location_id.id,
            'location_dest_id': picking_type.default_location_dest_id.id,
        })

        move_line = self.env['stock.move.line'].create({
            'move_id': move.id,
            'product_id': self.product_id.id,
            'qty_done': self.quantity,
            'lot_id': self.lot_id.id,
            'location_id': self.lot_id.location_id.id,
            'location_dest_id': picking_type.default_location_dest_id.id,
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id': picking.id,
            'target': 'current',
        }

        
    def open_stock_picking(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id('stock.stock_picking_action_picking_type')

        related_pickings = self.picking_id  # Asegúrate de que este campo exista

        action.update({
            'domain': [('id', 'in', related_pickings.ids)],
            'context': {
                'default_quality_alert_ids': [(4, self.id)],
            },
            'views': [(False, 'list'), (False, 'form')],
        })

        if len(related_pickings) == 1:
            action['views'] = [(False, 'form')]
            action['res_id'] = related_pickings.id

        return action


