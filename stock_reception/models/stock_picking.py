# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


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
        """
        for picking in self:
            picking.show_account_partner = picking.picking_type_id.code == 'incoming' 
            if picking.picking_type_id.barcode in ['NV1QC', 'NV1STOR']:
                picking.show_account_partner = True
            else:
                picking.show_account_partner = False

    @api.depends('account_partner_id')
    def _set_partner_and_owner(self):
        """Set the owner and account partner for the stock picking."""
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
        Also updates package state to 'done' for incoming pickings.
        """
        for picking in self:
            if not picking.user_id:
                picking.user_id = self.env.user
        
        res = super().button_validate()
        
        # If super() returned an action (wizard, confirmation, etc.), return it
        if res is not True and res:
            return res
        
        for picking in self:
            if picking.state != 'done':
                continue
                
            # Update package state to 'done' for validated incoming pickings
            if picking.picking_type_id.code == 'incoming':
                packages = picking.move_line_ids.mapped('result_package_id')
                packages_to_process = packages.filtered(lambda p: p.state and p.state != 'done')
                packages_to_process.write({'state': 'done'})
            
            # For QC pickings: mark packages as done (unpack will be done in storage action_assign)
            if picking.picking_type_id.barcode == 'WHQC':
                packages = picking.move_line_ids.mapped('package_id').filtered(lambda p: p)
                for package in packages:
                    if package.state and package.state != 'done':
                        package.write({'state': 'done'})
        
        return res
    
    def action_assign(self):
        """
        Override to preserve package reference when assigning storage pickings.
        After super() creates move_lines with package_id:
        1. Save package_id to origin_package_id
        2. Clear package_id to allow splitting
        3. Unpack the packages so products can be moved freely
        """
        res = super().action_assign()
        
        # For storage pickings: save origin_package_id, clear package_id, and unpack
        for picking in self:
            if picking.picking_type_id.barcode != 'WHSTOR':
                continue
            
            packages_to_unpack = self.env['stock.quant.package']
            
            for move_line in picking.move_line_ids:
                if move_line.package_id and not move_line.origin_package_id:
                    packages_to_unpack |= move_line.package_id
                    move_line.origin_package_id = move_line.package_id
                    move_line.package_id = False
            
            # Unpack all packages after saving references
            for package in packages_to_unpack:
                if package.quant_ids:
                    package.unpack()
        
        return res

