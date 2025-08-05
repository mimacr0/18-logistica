from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    maintenance_type = fields.Selection([
        ('repair', 'Repair'),
        ('review', 'Review'),
        ('warranty', 'Warranty'),
        ('renew', 'Renew'),
    ])
    picking_type_barcode = fields.Char(related="picking_type_id.barcode")

    def action_create_repair_order(self):
        RepairOrder = self.env['repair.order']

        for picking in self:
            if picking.maintenance_type in ['repair', 'warranty']:
                picking_type = self.env.ref('repair.picking_type_warehouse0_repair')
            elif picking.maintenance_type in ['renew', 'review']:
                picking_type = self.env.ref('repair_module.picking_type_warehouse0_review')
            else:
                raise ValidationError(_('Please select a maintenance type'))

            if not picking.move_line_ids:
                raise ValidationError(_('Introduce at least one product'))

            for line in picking.move_line_ids:
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
                }

                try:
                    if tracking == 'serial':
                        if not line.lot_id:
                            raise ValidationError(_("There are no selected lots"))

                        # Si tracking es 'serial', solo puede haber un lote por línea
                        RepairOrder.create({
                            **common_vals,
                            'product_qty': 1.0,
                            'lot_id': line.lot_id.id,
                            'lifecycle_state': line.lot_id.lifecycle_state,
                            'product_location_src_id': line.lot_id.location_id.id,
                        })

                    else:
                        RepairOrder.create({
                            **common_vals,
                            'product_qty': line.quantity,
                            'lot_id': False,
                        })

                except Exception as e:
                    raise ValidationError(_("Error creating repair order: %s") % str(e))

        return self.action_view_repairs()