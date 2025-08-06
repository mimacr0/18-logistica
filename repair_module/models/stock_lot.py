from odoo import models, fields, api, _
from .choices import LIFECYCLE_STATE

class StockLot(models.Model):
    _inherit = 'stock.lot'

    lifecycle_state = fields.Selection(LIFECYCLE_STATE, string='Lifecycle State')
    
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
