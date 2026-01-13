# -*- coding: utf-8 -*-
import pytz
from datetime import datetime
from odoo import models, fields, api, http, _


class RepairDiagnosis(models.Model):
    _name = 'repair.diagnosis'
    _description = "Repair Diagnosis"
    '''
        General list for the repair diagnosis, anybody can use them.
    '''
    name = fields.Char(translate=True)
    
    lot_ids = fields.Many2many(
        comodel_name='stock.lot',
        string='Related Lots',
        relation='stock_lot_repair_diagnosis_rel',
        column1='diagnosis_id',
        column2='lot_id'
    )