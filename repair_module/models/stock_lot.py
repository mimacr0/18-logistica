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
    
    repair_history = fields.Html(string='Repair History')
    repair_order_id = fields.Many2one('repair.order', string='Repair Order')

    diagnosis_ids = fields.Many2many(
        comodel_name='repair.diagnosis',
        string='Diagnosis',
        relation='stock_lot_repair_diagnosis_rel',
        column1='lot_id',
        column2='diagnosis_id'
    )

    result_ids = fields.Many2many(
        comodel_name='repair.result',
        string='Results',
        relation='stock_lot_repair_result_rel',
        column1='lot_id',
        column2='result_id'
    )
