from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta
from .choices import MAINTENANCE_TYPE


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    maintenance_type = fields.Selection(MAINTENANCE_TYPE, string='Maintenance Type')
    picking_type_barcode = fields.Char(related="picking_type_id.barcode")
    
    # Inverse Many2many relation with quality.alert (same table as picking_ids in quality.alert)
    repair_alert_ids = fields.Many2many(
        'quality.alert',
        'quality_alert_picking_rel',
        column1='stock_picking_id',
        column2='quality_alert_id',
        string='Repair Alerts'
    )

    @api.depends('picking_type_id', 'repair_alert_ids', 'quality_alert_ids')
    def _compute_show_account_partner(self):
        """Extend to show account_partner_id for repair-related pickings"""
        super()._compute_show_account_partner()
        repair_picking_type = self.env.ref('repair_module.stock_picking_type_move_to_repair', raise_if_not_found=False)
        for picking in self:
            if picking._is_repair_picking(repair_picking_type):
                picking.show_account_partner = True

    def _is_repair_picking(self, repair_picking_type=None):
        """Check if this picking is related to repairs (has repair alerts or is repair picking type)"""
        self.ensure_one()
        if repair_picking_type is None:
            repair_picking_type = self.env.ref('repair_module.stock_picking_type_move_to_repair', raise_if_not_found=False)
        return (
            self.repair_alert_ids or 
            self.quality_alert_ids.filtered('is_repair') or
            (repair_picking_type and self.picking_type_id == repair_picking_type)
        )

    def action_cancel(self):
        """Override to cancel related quality alerts when picking is cancelled"""
        res = super().action_cancel()
        
        # Get cancelled stage
        cancelled_stage = self.env.ref('repair_module.quality_alert_stage_repair_cancelled', raise_if_not_found=False)
        if not cancelled_stage:
            return res
        
        for picking in self:
            # Only apply to repair-related pickings
            if not picking._is_repair_picking():
                continue
            # Cancel related quality alerts (from Many2many relation)
            if picking.repair_alert_ids:
                picking.repair_alert_ids.write({'stage_id': cancelled_stage.id})
            # Also check One2many relation from quality_control (only repair alerts)
            repair_alerts = picking.quality_alert_ids.filtered('is_repair')
            if repair_alerts:
                repair_alerts.write({'stage_id': cancelled_stage.id})
        
        return res

    def button_validate(self):
        """Override to update related quality alerts to 'Sent for Repair' when picking is validated
        and automatically create repair orders"""
        res = super().button_validate()
        
        # Get sent for repair stage
        sent_stage = self.env.ref('repair_module.quality_alert_stage_sent_to_review_repair', raise_if_not_found=False)
        
        for picking in self:
            # Only update if picking is done and is repair-related
            if picking.state != 'done' or not picking._is_repair_picking():
                continue
            
            # Update related quality alerts stage
            if sent_stage:
                if picking.repair_alert_ids:
                    picking.repair_alert_ids.write({'stage_id': sent_stage.id})
                repair_alerts = picking.quality_alert_ids.filtered('is_repair')
                if repair_alerts:
                    repair_alerts.write({'stage_id': sent_stage.id})
            
            # Automatically create repair orders
            if picking.maintenance_type:
                picking.action_create_repair_order()
        
        return res

    def action_create_repair_order(self):
        RepairOrder = self.env['repair.order']

        for picking in self:
            if picking.maintenance_type in ['repair', 'warranty']:
                picking_type = self.env.ref('repair.picking_type_warehouse0_repair')
            elif picking.maintenance_type in ['renew', 'review']:
                picking_type = self.env.ref('repair_module.picking_type_warehouse0_review')
            else:
                raise ValidationError(_('Please select a maintenance type'))

            if not picking.move_ids:
                raise ValidationError(_('Introduce at least one product'))

            for line in picking.move_ids:
                if line.quantity <= 0.0:
                    raise ValidationError(_('The amount moved must be greater than 0'))

                product = line.product_id
                tracking = product.tracking
                alert_id = picking.quality_alert_ids[0] if picking.quality_alert_ids else False

                # Definir la fecha
                if alert_id and alert_id.schedule_date:
                    schedule_date = alert_id.schedule_date
                else:
                    schedule_date = fields.Date.today() + timedelta(days=7)

                common_vals = {
                    'account_partner_id': picking.account_partner_id.id,
                    'repair_alert_id': alert_id.id if alert_id else False,
                    'product_id': product.id,
                    'origin': picking.name,
                    'partner_id': picking.account_partner_id.partner_id.id,
                    'picking_id': picking.id,
                    'picking_type_id': picking_type.id,
                    'maintenance_type': picking.maintenance_type,
                    'under_warranty': picking.maintenance_type == 'warranty',
                    'schedule_date': schedule_date,
                    'description': alert_id.description if alert_id else False,
                }

                try:
                    if tracking == 'serial':
                        move_line = line.move_line_ids
                        if not move_line.lot_id:
                            raise ValidationError(_("There are no selected lots"))
                        # Si tracking es 'serial', solo puede haber un lote por línea
                        RepairOrder.create({
                            **common_vals,
                            'product_qty': 1.0,
                            'lot_id': move_line.lot_id.id,
                            'lifecycle_state': move_line.lot_id.lifecycle_state,
                            'product_location_src_id': move_line.location_id.id or picking.location_id.id,
                        })
                    elif tracking == 'none':
                        # Para productos sin serial, usar directamente line.quantity
                        RepairOrder.create({
                            **common_vals,
                            'product_qty': line.quantity,
                            'product_location_src_id': line.location_id.id or picking.location_id.id,
                        })

                except Exception as e:
                    raise ValidationError(_("Error creating repair order: %s") % str(e))

        return self.action_view_repairs()