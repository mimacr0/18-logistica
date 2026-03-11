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

    type = fields.Selection([
        ('return', 'Return Package'),
        ('new', 'New Package'),
    ], string='Type', default='new')

    rma_state = fields.Selection([
        ('draft', 'Received'),
        ('opened', 'Opened & Inspected'),
        ('done', 'Empty / Done'),
    ], string='RMA Status', default='draft', tracking=True)
    
    notes = fields.Text(string='Reception Notes')
    
    # Optional image capturing from the web backend
    image_1920 = fields.Image(string="Photo of the package")
    
    # Units that were found inside this package
    rma_unit_ids = fields.One2many(
        'rma.unit',
        'package_id',
        string="RMA Units inside"
    )

    rma_products_line_ids = fields.One2many(
        'rma.package.line',
        'package_id',
        string='RMA Products'
    )

    def action_unpack_rma(self):
        for package in self:
            if package.type != 'return':
                continue

            # Generate RMA units based on custom lines
            units_to_create = []
            
            # Filter only unpacked lines
            lines_to_unpack = package.rma_products_line_ids.filtered('unpacked')
            
            if not lines_to_unpack:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Info'),
                        'message': _('Nothing to unpack.'),
                        'type': 'warning',
                        'sticky': False,
                    }
                }
            
            for line in lines_to_unpack:
                # Create one unit per quantity
                for unit_idx in range(line.quantity):
                    units_to_create.append({
                        'package_id': package.id,
                        'product_id': line.product_map_id.product_id.id,
                        'owner_id': line.product_map_id.account_id.partner_id.id,
                        'state': 'received',
                    })
            
            # Mark the processed lines as packed efficiently in one query
            if lines_to_unpack:
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