# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.osv import expression
from datetime import datetime

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    account_partner_id = fields.Many2one(string='Owner Account', comodel_name='account.partner')

    # Campo genérico que otros módulos pueden extender
    show_account_partner = fields.Boolean(
        string='Show Account Partner',
        compute='_compute_show_account_partner',
        store=True,
        help='Determines if account_partner_id should be shown instead of partner_id'
    )


    @api.depends('picking_type_id')
    def _compute_show_account_partner(self):
        """
        Base computation for show_account_partner.
        Other modules can extend this by overriding and calling super().
        Example in another module:
            @api.depends('picking_type_id', 'other_field')
            def _compute_show_account_partner(self):
                super()._compute_show_account_partner()
                for picking in self:
                    if picking.some_condition:
                        picking.show_account_partner = True
        """
        for picking in self:
            # Por defecto, mostrar en recepciones
            picking.show_account_partner = picking.picking_type_id.code == 'incoming' 
            if picking.picking_type_id.barcode in ['NV1QC', 'NV1STOR']:
                picking.show_account_partner = True
            else:
                picking.show_account_partner = False



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

    def button_validate(self):
        """
        Override to assign current user as responsible when validating incoming pickings.
        """
        for picking in self:
            if not picking.user_id:
                picking.user_id = self.env.user
        return super().button_validate()

