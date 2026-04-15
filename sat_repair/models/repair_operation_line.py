# -*- coding: utf-8 -*-
from odoo import models, fields, api


class RepairOperationLine(models.Model):
    _name = 'repair.operation.line'
    _description = 'Repair Operation Line'

    repair_id = fields.Many2one('rma.repair', string='Repair', required=True, ondelete='cascade')
    product_id = fields.Many2one(
        'product.product',
        string='Service / Operation',
        required=True,
        ondelete='restrict',
        domain="[('type', '=', 'service')]",
        index=True,
    )
    name = fields.Char(string='Description')

    type = fields.Selection([
        ('diagnostic', 'Diagnostic'),
        ('fix', 'Fix / Operation'),
    ], string='Type', default='diagnostic', required=True)

    price_unit = fields.Float(string='Unit Price', digits='Product Price')
    notes = fields.Text(string='Notes')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.display_name
            self.price_unit = self.product_id.lst_price

    @api.model_create_multi
    def create(self, vals_list):
        Product = self.env['product.product']
        for vals in vals_list:
            pid = vals.get('product_id')
            if pid:
                p = Product.browse(pid)
                if p:
                    vals.setdefault('name', p.display_name)
                    vals.setdefault('price_unit', p.lst_price)
        return super().create(vals_list)
