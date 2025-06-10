
from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class CreateStockPickingLineWizard(models.TransientModel):
    _name = 'create.stock.picking.line.wizard'
    _description = 'Create Stock Picking Line Wizard'

    package_reception_id = fields.Many2one(string='Package Reception', comodel_name='create.stock.picking.wizard')
    product_id = fields.Many2one(string='Product', comodel_name='product.product')
    product_uom_qty = fields.Float(string='Quantity')
    location_id = fields.Many2one(string='Location', comodel_name='stock.location', default=lambda self: self.env.ref('stock.stock_location_customers').id)
    location_dest_id = fields.Many2one(string='Destination Location', comodel_name='stock.location', default=lambda self: self.env.ref('stock.stock_location_company').id)
    account_partner_id = fields.Many2one(string='Owner Account', comodel_name='account.partner')
    box_number = fields.Integer(string='Box Number')