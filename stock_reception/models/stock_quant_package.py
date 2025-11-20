# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

#Esto esta comentado en el init, por lo que no se está implementado en el modulo de stock_reception

from odoo import api, fields, models, _
from odoo.osv import expression
from datetime import datetime

class QuantPackage(models.Model):
    _name = 'stock.quant.package'
    _inherit = ['stock.quant.package', 'mail.thread', 'mail.activity.mixin']

    carrier_tracking_ref = fields.Char(string='Carrier Tracking Reference')
    global_tracking_ref = fields.Char(string='International Tracking Reference')
    carrier_id = fields.Many2one(string='Carrier', comodel_name='delivery.carrier')
    carrier_name = fields.Char(string='Carrier Name')
    optional_tracking_ref = fields.Char(string='Optional Tracking Reference')
    
    # @api.model
    # def set_name_based_on_account(self, account):
    #     """
    #     Genera y devuelve un nombre único para el paquete usando la secuencia definida.
    #     La secuencia incluye automáticamente la fecha (YYMMDD) y un número secuencial.
    #     """
    #     if not account:
    #         return ''
    #     # Usar la secuencia definida en stock_package_sequence.xml
    #     # El prefijo %(y)s%(month)s%(day)s genera automáticamente YYMMDD
    #     # El padding de 3 genera números como 001, 002, etc.
    #     name = self.env['ir.sequence'].next_by_code('stock.quant.package.custom')
    #     if not name:
    #         # Fallback si la secuencia no existe
    #         date_str = datetime.now().strftime('%y%m%d')
    #         name = f"{date_str}001"
    #     return name