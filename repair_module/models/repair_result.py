# -*- coding: utf-8 -*-
import pytz
from datetime import datetime
from odoo import models, fields, api, http, _


class RepairResult(models.Model):
    _name = 'repair.result'
    _description = "Repair Results"
    '''
        General list for the repair result, anybody can use them.
    '''
    name = fields.Char(translate=True)
    
    lot_ids = fields.Many2many(
        comodel_name='stock.lot',
        string='Related Lots',
        relation='stock_lot_repair_result_rel',
        column1='result_id',
        column2='lot_id'
    )

    price = fields.Float(string='Price')