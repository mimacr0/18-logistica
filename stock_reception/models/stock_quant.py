# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.osv import expression
from datetime import datetime

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    account_partner_id = fields.Many2one(string='Owner Account', comodel_name='account.partner')

    @api.depends('owner_id')
    def _compute_account_partner_id(self):
        """
        Compute the account_partner_id field for stock quants.
        This method sets the account_partner_id based on the owner_id of the quant.
        """
        for record in self:
            if record.owner_id:
                account_partner = self.env['account.partner'].search([('partner_id', '=', record.owner_id.res_partner.id)], limit=1)
                record.account_partner_id = account_partner
            else:
                record.account_partner_id = False