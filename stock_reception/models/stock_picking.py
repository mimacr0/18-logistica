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

    # -------------------------------------------------------------------------
    # Button Validate - Process completed pickings
    # -------------------------------------------------------------------------

    def button_validate(self):
        """
        Override to assign current user as responsible NV1en validating pickings.
        Also updates package state to 'done' for incoming pickings.
        For incoming pickings: unpack QC pickings after validation.
        """
        self._assign_user_if_missing()
        
        res = super().button_validate()
        
        # If super() returned an action (wizard, confirmation, etc.), return it
        if res is not True and res:
            return res
        
        self._process_validated_pickings()
        
        return res

    def _assign_user_if_missing(self):
        """Assign current user as responsible if not already set."""
        for picking in self:
            if not picking.user_id:
                picking.user_id = self.env.user

    def _process_validated_pickings(self):
        """Process pickings after validation is complete."""
        for picking in self:
            if picking.state != 'done':
                continue
            
            picking._update_package_state_for_incoming()
            picking._unpack_qc_pickings_after_reception()
            picking._mark_qc_packages_as_done()

    def _update_package_state_for_incoming(self):
        """Update package state to 'done' for validated incoming pickings."""
        self.ensure_one()
        if self.picking_type_id.code == 'incoming':
            packages = self.move_line_ids.mapped('result_package_id')
            packages_to_process = packages.filtered(lambda p: p.state and p.state != 'done')
            packages_to_process.write({'state': 'done'})

    def _unpack_qc_pickings_after_reception(self):
        """
        After validating a reception, find and unpack the QC pickings.
        This is called from reception picking after push rules create QC picking.
        """
        self.ensure_one()
        if self.picking_type_id.code != 'incoming':
            return
        
        # Find QC pickings created by push rules (same group_id)
        if not self.group_id:
            return
        
        qc_pickings = self.env['stock.picking'].search([
            ('picking_type_id.barcode', '=', 'NV1QC'),
            ('state', 'not in', ['done', 'cancel']),
            ('group_id', '=', self.group_id.id),
        ])
        
        for qc_picking in qc_pickings:
            qc_picking._unpack_for_qc()

    def _unpack_for_qc(self):
        """
        Unpack packages at the start of QC to allow free movement.
        - Save package_id to origin_package_id
        - Clear package_id and result_package_id
        - Unpack the physical packages
        """
        self.ensure_one()
        packages_to_unpack = self.env['stock.quant.package']
        
        for move_line in self.move_line_ids:
            # Save origin_package_id if not already set
            if move_line.package_id and not move_line.origin_package_id:
                move_line.origin_package_id = move_line.package_id
                packages_to_unpack |= move_line.package_id
            
            # Clear package references to allow free movement
            if move_line.package_id:
                move_line.package_id = False
            if move_line.result_package_id:
                move_line.result_package_id = False
        
        # Unpack physical packages
        self._unpack_packages(packages_to_unpack)

    def _mark_qc_packages_as_done(self):
        """Mark packages as done NV1en QC is validated."""
        self.ensure_one()
        if self.picking_type_id.barcode != 'NV1QC':
            return
        
        # Get packages from origin_package_id since package_id was cleared
        packages = self.move_line_ids.mapped('origin_package_id').filtered(lambda p: p)
        self._mark_packages_as_done(packages)

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _mark_packages_as_done(self, packages):
        """Mark packages as done if they have a state field."""
        for package in packages:
            if package.state and package.state != 'done':
                package.write({'state': 'done'})

    def _unpack_packages(self, packages):
        """Unpack packages that still have quants."""
        for package in packages:
            if package.quant_ids:
                package.unpack()
