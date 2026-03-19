# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2026 DaFe Solutions
#
##############################################################################

from odoo import models, fields, api, _

class StockQuantPackage(models.Model):
    _name = 'stock.quant.package'
    _inherit = ['stock.quant.package', 'mail.thread', 'mail.activity.mixin']

    carrier_id = fields.Many2one(
        'delivery.carrier',
        string='Carrier',
        tracking=True
    )
    sender_id = fields.Many2one('res.partner', string='Sender')
    shipping_address_id = fields.Many2one(
        'res.partner',
        string='Shipping Address',
        domain="[('type', 'in', ['delivery', 'other', 'contact'])]"
    )
    customer_reference = fields.Char(string='Customer Reference')
    number_of_packages = fields.Integer(string='Number of Packages', default=1)
    sale_id = fields.Many2one('sale.order', 'Pedido de Venta')
    
    type = fields.Selection([
        ('return', 'Return Package'),
        ('new', 'New Package'),
    ], string='Type', default='new')

    rma_state = fields.Selection([
        ('draft', 'Waiting Package'),
        ('opened', 'Opened & Inspected'),
        ('done', 'Empty / Done'),
    ], string='RMA Status', default='draft', tracking=True)
    notes = fields.Text(string='Reception Notes')

    # Dimensions for the specific package instance
    height = fields.Float('Height', help="Packaging Height")
    width = fields.Float('Width', help="Packaging Width")
    packaging_length = fields.Float('Length', help="Packaging Length")
    
    # Optional image capturing from the web backend
    image_1920 = fields.Image(string="Photo of the package")
    
    # Units that were found inside this package
    rma_unit_ids = fields.One2many(
        'rma.unit',
        'package_id',
        string="RMA Units inside"
    )

    package_products_line_ids = fields.One2many(
        'rma.package.line',
        'package_id',
        string='RMA Products'
    )

    def _get_lines_to_unpack(self, package):
        """Returns the unpacked lines for a package, or a warning notification dict if none."""
        lines = package.package_products_line_ids.filtered(lambda l: l.unpacked)
        if not lines:
            return None, {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Info'),
                    'message': _('Nothing to unpack.'),
                    'type': 'warning',
                    'sticky': False,
                }
            }
        return lines, None

    def action_unpack_rma(self):
        for package in self:
            if package.type != 'return':
                continue

            lines_to_unpack, warning = self._get_lines_to_unpack(package)
            if warning:
                return warning

            units_to_create = []
            for line in lines_to_unpack:
                # Create one unit per quantity
                for unit_idx in range(line.quantity):
                    units_to_create.append({
                        'package_id': package.id,
                        'product_id': line.product_map_id.product_id.id,
                        'owner_id': line.product_map_id.account_id.partner_id.id,
                        'state': 'received',
                        'location_id': package.location_id.id or self.env.ref('stock.stock_location_stock').id
                    })

            # Mark the processed lines as packed efficiently in one query
            lines_to_unpack.write({'unpacked': False})
            if units_to_create:
                self.env['rma.unit'].create(units_to_create)
            
            # Mark as opened
            package.rma_state = 'opened'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('All items unpacked successfully.'),
                'type': 'success',
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def action_unpack_quant(self):
        for package in self:
            if package.type != 'new':
                continue

            quants_to_create = []

            # Filtrar solo líneas no desempaquetadas
            lines_to_unpack, warning = self._get_lines_to_unpack(package)
            if warning:
                return warning

            for line in lines_to_unpack:
                quants_to_create.append({
                    'product_id': line.product_map_id.product_id.id,
                    'location_id': package.location_id.id or self.env.ref('stock.stock_location_stock').id,
                    'package_id': package.id,
                    'quantity': line.quantity,
                    'owner_id': line.product_map_id.account_id.partner_id.id,
                })


            # Marcar líneas como procesadas
            lines_to_unpack.write({'unpacked': False})

            if quants_to_create:
                self.env['stock.quant'].create(quants_to_create)

            package.rma_state = 'opened'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('All items unpacked successfully.'),
                'type': 'success',
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }


class RmaPackageLine(models.Model):
    _name = 'rma.package.line'
    _description = 'Líneas de los Paquetes RMA'

    package_id = fields.Many2one(
        'stock.quant.package',
        string='Paquete',
        ondelete='cascade'
    )
    product_map_id = fields.Many2one(
        'account.product.map',
        string='Producto de Cliente',
        required=True
    )
    quantity = fields.Integer(
        string='Cantidad',
        default=1
    )

    unpacked = fields.Boolean(string='Unpacked', default=True)