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