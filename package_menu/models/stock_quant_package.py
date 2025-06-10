# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.osv import expression
from datetime import datetime

class QuantPackage(models.Model):
    _name = 'stock.quant.package'
    _inherit = ['stock.quant.package', 'mail.thread', 'mail.activity.mixin']

    account_partner_id = fields.Many2one(string='Owner Account', comodel_name='account.partner')
    
    @api.model
    def set_name_based_on_account(self, account):
        """
        Genera y devuelve un nombre único para el paquete basado en la cuenta.
        Si ya existe un paquete con ese nombre, incrementa la secuencia en la cuenta
        y genera un nuevo nombre.
        """
        if not account:
            return ''
        date_str = datetime.now().strftime('%Y%m%d')
        sequence = str(account.reception_sequence).zfill(4)
        name = f"{account.name}{date_str}{sequence}"
        # Buscar paquete con ese nombre
        package = self.search([('name', '=', name)], limit=1)
        if package:
            # Incrementar secuencia en cuenta y regenerar nombre
            account._increase_reception_sequence()
            sequence = str(account.reception_sequence).zfill(4)
            name = f"{account.name}{date_str}{sequence}"
        return name