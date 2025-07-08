from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    maintenance_type = fields.Selection([
        ('repair', 'Repair'),
        ('review', 'Review'),
        ('warranty', 'Warranty'),
        ('renew', 'Renew'),
    ])

    def action_create_repair_order(self):
        RepairOrder = self.env['repair.order']

        for picking in self:

            if picking.maintenance_type in ['repair', 'warranty']:
                picking_type = self.env.ref('repair.picking_type_warehouse0_repair')
            elif  picking.maintenance_type in ['renew', 'review']:
                picking_type = self.env.ref('repair_module.picking_type_warehouse0_review')

            if not picking.move_line_ids:
                raise ValidationError(_('Introduce at least one product'))

            for line in picking.move_line_ids:
                if line.quantity <= 0.0:
                    raise ValidationError(_('The amount moved must be greater than 0'))

                product = line.product_id
                tracking = product.tracking

                common_vals = {
                    'account_partner_id': picking.account_partner_id.id,
                    'product_id': product.id,
                    'origin': picking.name,
                    'partner_id': picking.partner_id.id,
                    'picking_id': picking.id,
                    'picking_type_id': picking_type.id,
                    'maintenance_type': picking.maintenance_type,
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