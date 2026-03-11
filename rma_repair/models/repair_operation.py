# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class RepairOperationLine(models.Model):
    _name = 'repair.operation.line'
    _description = 'Repair Operation Line'

    repair_id = fields.Many2one('rma.repair', string='Repair', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Service/Operation', domain="[('type', '=', 'service')]", required=True)
    name = fields.Char(string='Description', related='product_id.name', readonly=False)
    
    type = fields.Selection([
        ('diagnostic', 'Diagnostic'),
        ('fix', 'Fix / Operation'),
    ], string='Type', default='diagnostic', required=True)
    
    price_unit = fields.Float(string='Unit Price', related='product_id.list_price', readonly=False)
    notes = fields.Text(string='Notes')
