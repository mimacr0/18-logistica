# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.osv import expression
from datetime import datetime

class QuantPackage(models.Model):
    _name = 'stock.quant.package'
    _inherit = ['stock.quant.package', 'mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    account_partner_id = fields.Many2one(string='Owner Account', comodel_name='account.partner')
    reception_hours = fields.Float(string='Reception Hours', compute='_compute_reception_hours')
    reception_hours_label = fields.Char(string='Reception Hours Label', compute='_compute_reception_hours')
    state = fields.Selection([
        ('planned', 'Planned'),
        ('on_hold', 'On Hold'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('with_incidence', 'Incidence'),
        ('cancelled', 'Cancelled')
    ], copy=False, default='on_hold', store=True, tracking=True)
    carrier_tracking_ref = fields.Char(string='Carrier Tracking Reference')
    global_tracking_ref = fields.Char(string='International Tracking Reference')
    carrier_id = fields.Many2one(string='Carrier', comodel_name='delivery.carrier')
    carrier_name = fields.Char(string='Carrier Name')
    optional_tracking_ref = fields.Char(string='Optional Tracking Reference')
    
    @api.model
    def set_name_based_on_account(self, account):
        """
        Genera y devuelve un nombre único para el paquete usando la secuencia definida.
        La secuencia incluye automáticamente la fecha (YYMMDD) y un número secuencial.
        """
        if not account:
            return ''
        # Usar la secuencia definida en stock_package_sequence.xml
        # El prefijo %(y)s%(month)s%(day)s genera automáticamente YYMMDD
        # El padding de 3 genera números como 001, 002, etc.
        name = self.env['ir.sequence'].next_by_code('stock.quant.package.custom')
        if not name:
            # Fallback si la secuencia no existe
            date_str = datetime.now().strftime('%y%m%d')
            name = f"{date_str}001"
        return name


    
    def _compute_reception_hours(self):
        ct = datetime.now()
        for record in self:
            if record.state != 'on_hold':
                record.reception_hours = 0
                record.reception_hours_label = 'Received'
                continue
            if record.create_date:
                record.reception_hours = (ct - record.create_date).total_seconds() / 3600
                record.reception_hours_label = f'{int(record.reception_hours)}h {int(record.reception_hours % 1 * 60)}m'
            else:
                record.reception_hours = 0
                record.reception_hours_label = '0h 0m'