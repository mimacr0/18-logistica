# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.osv import expression
from datetime import datetime

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    account_partner_id = fields.Many2one(string='Owner Account', comodel_name='account.partner')

    is_reception = fields.Boolean(string='Is Reception', compute='_compute_is_reception', store=True)

    @api.depends('picking_type_id')
    def _compute_is_reception(self):
        for picking in self:
            picking.is_reception = picking.picking_type_id.code == 'incoming' 


    @api.depends('account_partner_id')
    def _set_partner_and_owner(self):
        """
        Set the owner and account partner for the stock picking.
        """
        for picking in self:
            if picking.account_partner_id:
                picking.partner_id = picking.account_partner_id.partner_id
                picking.owner_id = picking.account_partner_id.partner_id
            else:
                picking.partner_id = False
                picking.owner_id = False

