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
    is_repair = fields.Boolean(string='Is Repair', default=False)
    is_locked = fields.Boolean(default=True)


    def write(self, vals):
        for alert in self:
            messages = []

            # Detectar cambio de bloqueo
            if 'is_locked' in vals and vals['is_locked'] != alert.is_locked:
                state = 'locked' if vals['is_locked'] else 'unlocked'
                messages.append(_("Alert has been %s by %s") % (state, self.env.user.name))

            # Detectar cambio de etapa
            if 'stage_id' in vals and vals['stage_id'] != alert.stage_id.id:
                new_stage = self.env['quality.alert.stage'].browse(vals['stage_id']).name
                messages.append(_("Stage changed to '%s' by %s") % (new_stage, self.env.user.name))

            # Llamar al super write primero
            res = super(QualityAlert, alert).write(vals)

            # Publicar mensajes en el chatter
            for msg in messages:
                alert.message_post(body=msg)

        return res
        
    def toggle_lock(self):
        """ Alterna el valor de is_locked """
        for record in self:
            record.is_locked = not record.is_locked

    @api.depends('picking_ids')
    def _compute_picking_id(self):
        for record in self:
            record.picking_id = record.picking_ids[:1] if record.picking_ids else False

    def _compute_stock_picking_count(self):
        for picking in self:
            picking.stock_picking_count = len(self.picking_ids)

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
            raise ValidationError(_('Quantity must be greater than 0.'))

        if not self.product_id:
            raise ValidationError(_('A product must be selected.'))

        if not self.lot_id:
            raise ValidationError(_('A lot must be selected.'))
        picking_type = self.env.ref('repair_module.stock_picking_type_move_to_repair')
        
        total_qty_to_move = self.quantity
        picking_created = False
        
        # Crear el picking solo una vez
        picking = self.env['stock.picking'].create({
            'origin': self.name,
            'picking_type_id': picking_type.id,
            'location_id':  self.env.ref('stock.stock_location_stock').id,
            'location_dest_id': picking_type.default_location_dest_id.id,
            'quality_alert_ids': [(6, 0, [self.id])],
            'maintenance_type': self.maintenance_type,
        })
        
        for quant in self.lot_id.quant_ids:
            available_qty = quant.quantity - quant.reserved_quantity
            if available_qty <= 0:
                continue  # saltar quants sin stock disponible
            
            qty_to_move = min(total_qty_to_move, available_qty)
            
            # Crear move para cada quant
            move = self.env['stock.move'].create({
                'name': quant.product_id.display_name,
                'product_id': quant.product_id.id,
                'product_uom_qty': qty_to_move,
                'product_uom': quant.product_id.uom_id.id,
                'picking_id': picking.id,
                'location_id': quant.location_id.id,
                'location_dest_id': picking_type.default_location_dest_id.id,
            })
            
            # Crear move line
            self.env['stock.move.line'].create({
                'move_id': move.id,
                'product_id': quant.product_id.id,
                'lot_id': quant.lot_id.id,
                'qty_done': qty_to_move,
                'location_id': quant.location_id.id,
                'location_dest_id': picking_type.default_location_dest_id.id,
            })
            
            total_qty_to_move -= qty_to_move
            if total_qty_to_move <= 0:
                break  # ya movimos toda la cantidad requerida
        
        if total_qty_to_move > 0:
            raise ValidationError(_('Not enough quantity available in the selected lots. Remaining: %s') % total_qty_to_move)
        
        # Asociar el picking al registro
        self.write({'picking_ids': [(4, picking.id)]})
        
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

        related_pickings = self.picking_ids  # Asegúrate de que este campo exista

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


