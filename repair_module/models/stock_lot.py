from odoo import models, fields, api, _

class StockLot(models.Model):
    _inherit = 'stock.lot'

    lifecycle_state = fields.Selection([
        ('A', 'A-Awaiting Inspection'),
        ('B', 'B-New'),
        ('C', 'C-Semi-new'),
        ('D', 'D-Repair'),
        ('E', 'E-Scrap'),
        ('F', 'F-Repair in review') 
    ], string='Lifecycle State')
