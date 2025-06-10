from datetime import datetime
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class CreateStockPickingWizard(models.TransientModel):
    _name = 'create.stock.picking.wizard'
    _description = 'Create Stock Picking Wizard'


    @api.model
    def default_get(self, fields):
        res = super(CreateStockPickingWizard, self).default_get(fields)
        product_ids = self.env.context.get('active_ids', [])  # Obtener los IDs de productos activos
        product_records = self.env['product.product'].browse(product_ids)
        partner_ids = product_records.mapped('account_partner_id')
        if not partner_ids:
            raise ValidationError("No se han encontrado partners asociados a los productos seleccionados.")
        if len(partner_ids) > 1:
            raise ValidationError("Los productos seleccionados tienen diferentes partners asociados. Deben ser iguales.")
        lines = []
        # count = 1

        for product_id in product_ids:
            lines.append((0, 0, {
                'product_id': product_id,
                'product_uom_qty': 0,
                'account_partner_id': partner_ids[0].id,
                'location_id': self.env.ref('stock.stock_location_customers').id,
                'location_dest_id': self.env.ref('stock.stock_location_company').id,
                # 'box_number': count,
                'box_number': 1,
            }))
            # count += 1
        res['reception_line_ids'] = lines
        res['account_partner_id'] = partner_ids[0].id
        res['location_id'] = self.env.ref('stock.stock_location_customers').id
        res['location_dest_id'] = self.env.ref('stock.stock_location_company').id
        res['picking_type_id'] = self.env.ref('stock.picking_type_in').id
        return res

    account_partner_id = fields.Many2one(string='Owner Account', comodel_name='account.partner')
    # package_name = fields.Char(string='Package Name')
    package_type_id = fields.Many2one(string='Package Type', comodel_name='stock.package.type')
    location_id = fields.Many2one(string='Location', comodel_name='stock.location')
    pack_date = fields.Date('Pack Date', default=fields.Date.today)
    height = fields.Char(string='Height', help="Packaging Height")
    width = fields.Char(string='Width', help="Packaging Width")
    packaging_length = fields.Char(string='Length', help="Packaging Length")
    packaging_weight = fields.Float(string='Weight', help="Packaging Weight")
    carrier_name = fields.Char(string='Carrier Name')
    carrier_id = fields.Many2one(string='Carrier', comodel_name='delivery.carrier')
    global_tracking_ref = fields.Char(string='International Tracking Reference')
    optional_tracking_ref = fields.Char(string='Optional Tracking Reference')
    picking_type_id = fields.Many2one(string='Picking Type', comodel_name='stock.picking.type')
    location_dest_id = fields.Many2one(string='Destination Location', comodel_name='stock.location')
    scheduled_date = fields.Date(string='Scheduled Date')
    reception_line_ids = fields.One2many(string='Package Lines', comodel_name='create.stock.picking.line.wizard', inverse_name='package_reception_id')

    @api.onchange('package_type_id')
    def _compute_measures(self):
        for record in self:
            if record.package_type_id:
                record.height = record.package_type_id.height
                record.width = record.package_type_id.width
                record.packaging_length = record.package_type_id.packaging_length
                record.packaging_weight = record.package_type_id.base_weight

    def _check_reception_information(self):
        for record in self:
            if not record.package_type_id:
                raise ValidationError(_('Please select a package type.'))
            if not record.global_tracking_ref:
                raise ValidationError(_('Please introduce a carrier_tracking_ref.'))
            if not record.scheduled_date:
                raise ValidationError(_('Please enter a scheduled date.'))
            if not record.reception_line_ids:
                raise ValidationError(_('Please add at least one reception line.'))
            return True

    def action_create_package(self, account_partner_id=None):
        for record in self:
            package_name = self.env['stock.quant.package'].set_name_based_on_account(account_partner_id)

            package_values = {
                'name': package_name,
                'package_type_id': record.package_type_id.id,
                'account_partner_id': record.account_partner_id.id,
                'owner_id': record.account_partner_id.partner_id.id,
                'location_id': record.location_dest_id.id,
                'pack_date': record.pack_date,
                'global_tracking_ref': record.global_tracking_ref,
                'carrier_name': record.carrier_name or '',
                'carrier_id': record.carrier_id.id or False,
                'optional_tracking_ref': record.optional_tracking_ref or '',
            }
            package = self.env['stock.quant.package'].create(package_values)
            return package, package_name

    def action_new_reception(self):
        for record in self:
            record._check_reception_information()
            
            partner_id = record.account_partner_id.partner_id.id
            picking_vals = {
                'account_partner_id': record.account_partner_id.id,
                'owner_id': partner_id,
                'partner_id': partner_id,
                'picking_type_id': record.picking_type_id.id,
                'location_id': record.location_id.id,
                'location_dest_id': record.location_dest_id.id,
                'scheduled_date': record.scheduled_date,
            }
            picking = self.env['stock.picking'].create(picking_vals)

            packages_name = []
            move_vals_list = []
            move_box_nums = []
            box_package_map = {}
            packages_ids = []

            for line in record.reception_line_ids:
                box_num = line.box_number
                product_weight = line.product_id.weight * line.product_uom_qty  # Calcular peso del producto
                if box_num not in box_package_map:
                    package, package_name = record.action_create_package(record.account_partner_id)
                    packages_name.append(package_name)
                    box_package_map[box_num] = {'package': package, 'total_weight': 0}  # Inicializar peso total
                    packages_ids.append(package.id)
                # Sumar el peso del producto al peso total del paquete
                box_package_map[box_num]['total_weight'] += product_weight
                move_vals = {
                    'name': line.product_id.name or _('Move'),
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.product_uom_qty,
                    'quantity': line.product_uom_qty,
                    'product_uom': line.product_id.uom_id.id,
                    'location_id': line.location_id.id,
                    'location_dest_id': line.location_dest_id.id,
                    'picking_id': picking.id,
                    'date': record.scheduled_date,
                    'state': 'draft',
                }
                move_vals_list.append(move_vals)
                move_box_nums.append(box_num)
                
            # Batch create moves
            stock_moves = self.env['stock.move'].create(move_vals_list)

            # Assign packages to move lines according to box number association retained
            for stock_move, box_num in zip(stock_moves, move_box_nums):
                package_info = box_package_map.get(box_num)
                if package_info:
                    package = package_info['package']
                    for move_line in stock_move.move_line_ids:
                        move_line.write({
                            'result_package_id': package.id,
                            'owner_id': partner_id,
                        })
                    package.write({
                        'shipping_weight': package_info['total_weight'] + package.package_type_id.base_weight,
                    })

            total_shipping_weight = sum(line.product_id.weight * line.product_uom_qty for line in record.reception_line_ids)
            packages_name_str = ', '.join(packages_name)

            picking.write({
                'state': 'confirmed',
                'shipping_weight': total_shipping_weight,
                'origin': packages_name_str,
            })

        return {
            'name': _('Created Packages'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.quant.package',
            'view_mode': 'list,form',
            'res_id': picking.id,
            'target': 'current',
            'domain': [('id', 'in', packages_ids)],
        }

        # action = self.env.ref('stock.action_product_stock_view').read()[0]
        # action['view_mode'] = 'list'  # o el dominio que desees
        # return action