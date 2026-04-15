# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero


class RmaRepairAddPartsWizard(models.TransientModel):
    _name = 'rma.repair.add.parts.wizard'
    _description = 'Wizard to add spare parts'

    repair_id = fields.Many2one('rma.repair', string='Repair', required=True)
    owner_id = fields.Many2one('res.partner', related='repair_id.owner_id')
    line_ids = fields.One2many(
        'rma.repair.add.parts.wizard.line',
        'wizard_id',
        string='Lines',
    )

    def action_add_parts(self):
        self.ensure_one()
        if not self.line_ids:
            return {'type': 'ir.actions.act_window_close'}

        dest_location = self.env.ref(
            'rma_inventory.stock_location_rma_repair_department_warehouse',
            raise_if_not_found=False,
        )
        if not dest_location:
            raise UserError(
                _('The repair department warehouse location is missing. Update module RMA Inventory.')
            )

        quant_ids_to_link = []
        for line in self.line_ids:
            if not line.product_id or not line.location_id:
                continue
            quants = line._quants_for_selection().sorted('id')
            if not quants:
                raise UserError(
                    _('No stock found for %(product)s at %(location)s.')
                    % {'product': line.product_id.display_name, 'location': line.location_id.display_name}
                )
            if float_is_zero(line.qty_to_add, precision_rounding=line.product_id.uom_id.rounding):
                continue

            total_avail = sum(quants.mapped('available_quantity'))
            prec = line.product_id.uom_id.rounding
            if float_compare(line.qty_to_add, total_avail, precision_rounding=prec) > 0:
                raise UserError(
                    _('Quantity to add (%(qty)s) cannot exceed available quantity (%(avail)s) for %(product)s.')
                    % {'qty': line.qty_to_add, 'avail': total_avail, 'product': line.product_id.display_name}
                )
            if float_compare(line.qty_to_add, 0, precision_rounding=prec) <= 0:
                raise UserError(_('Quantity to add must be positive.'))

            remaining = line.qty_to_add
            for quant in quants:
                if float_is_zero(remaining, precision_rounding=prec):
                    break
                avail = quant.available_quantity
                if float_is_zero(avail, precision_rounding=quant.product_uom_id.rounding):
                    continue
                take = min(remaining, avail)
                qprec = quant.product_uom_id.rounding
                if float_compare(take, avail, precision_rounding=qprec) == 0:
                    quant_ids_to_link.append(quant.id)
                else:
                    # Parcial: albarán interno hacia el almacén de reparaciones. Si el quant ya está ahí,
                    # origen = destino y no hay movimiento posible (no implementamos fraccionamiento in situ).
                    if quant.location_id == dest_location:
                        raise UserError(_(
                            'No puede añadir una cantidad parcial desde la ubicación del almacén de '
                            'reparaciones: el sistema movería el stock hacia la misma ubicación. '
                            'Indique la cantidad total disponible en esta línea, o mueva antes el '
                            'material a otra ubicación y añádalo desde ahí.'
                        ))
                    new_q = line._transfer_partial_quant_to_repair_location(quant, take, dest_location)
                    if not new_q:
                        raise UserError(
                            _('Could not complete internal transfer for %(product)s. Check stock configuration.')
                            % {'product': quant.product_id.display_name}
                        )
                    quant_ids_to_link.append(new_q.id)
                remaining -= take

        if quant_ids_to_link:
            self.repair_id.write({
                'spare_part_ids': [(4, qid) for qid in quant_ids_to_link],
            })
        return {'type': 'ir.actions.act_window_close'}


class RmaRepairAddPartsWizardLine(models.TransientModel):
    _name = 'rma.repair.add.parts.wizard.line'
    _description = 'Add spare parts wizard line'

    @api.model
    def _default_repair_department_location_id(self):
        """Almacén de repuestos del departamento de reparaciones (mismo destino del movimiento interno)."""
        return self.env.ref(
            'rma_inventory.stock_location_rma_repair_department_warehouse',
            raise_if_not_found=False,
        )

    wizard_id = fields.Many2one('rma.repair.add.parts.wizard', string='Wizard', required=True, ondelete='cascade')
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        domain="[('product_tmpl_id.is_spare_parts', '=', True), ('type', '!=', 'service')]",
    )
    allowed_location_ids = fields.Many2many(
        'stock.location',
        string='Allowed locations',
        compute='_compute_allowed_location_ids',
    )
    location_id = fields.Many2one(
        'stock.location',
        string='From location',
        required=True,
        default=_default_repair_department_location_id,
    )
    qty_available = fields.Float(
        string='Available',
        compute='_compute_qty_available',
        digits='Product Unit of Measure',
    )
    qty_to_add = fields.Float(string='Quantity to add', digits='Product Unit of Measure', default=1.0)

    @api.depends('product_id', 'wizard_id.owner_id')
    def _compute_allowed_location_ids(self):
        Location = self.env['stock.location']
        repair_loc = self.env.ref(
            'rma_inventory.stock_location_rma_repair_department_warehouse',
            raise_if_not_found=False,
        )
        for line in self:
            if not (line.product_id and line.wizard_id.owner_id):
                line.allowed_location_ids = repair_loc if repair_loc else Location
                continue
            locs = self.env['stock.quant'].search([
                ('owner_id', '=', line.wizard_id.owner_id.id),
                ('product_id', '=', line.product_id.id),
                ('quantity', '>', 0),
            ]).mapped('location_id')
            if repair_loc:
                locs = locs | repair_loc
            line.allowed_location_ids = locs

    @api.depends('product_id', 'location_id', 'wizard_id.owner_id')
    def _compute_qty_available(self):
        for line in self:
            if not (line.product_id and line.location_id and line.wizard_id.owner_id):
                line.qty_available = 0.0
                continue
            quants = line._quants_for_selection()
            line.qty_available = sum(quants.mapped('available_quantity'))

    def _quants_for_selection(self):
        self.ensure_one()
        return self.env['stock.quant'].search([
            ('owner_id', '=', self.wizard_id.owner_id.id),
            ('product_id', '=', self.product_id.id),
            ('location_id', '=', self.location_id.id),
            ('quantity', '>', 0),
        ])

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.location_id = self._default_repair_department_location_id()
        quants = self._quants_for_selection()
        if quants:
            self.qty_to_add = sum(quants.mapped('available_quantity'))
        else:
            self.qty_to_add = 0.0

    @api.onchange('location_id')
    def _onchange_location_id(self):
        quants = self._quants_for_selection()
        if quants:
            self.qty_to_add = sum(quants.mapped('available_quantity'))
        else:
            self.qty_to_add = 0.0

    def _transfer_partial_quant_to_repair_location(self, quant, qty_to_take, dest_location):
        """Move qty_to_take from quant's location to dest via internal picking; return destination quant to link."""
        self.ensure_one()
        if quant.location_id == dest_location:
            raise UserError(_(
                'No puede moverse una cantidad parcial hacia el almacén de reparaciones cuando el '
                'stock ya está en esa ubicación (origen y destino coinciden).'
            ))
        picking_type = self.env.ref('stock.picking_type_internal', raise_if_not_found=False)
        if not picking_type:
            raise UserError(_('Internal operation type (stock) is not available.'))

        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'location_id': quant.location_id.id,
            'location_dest_id': dest_location.id,
            'company_id': quant.company_id.id,
            'origin': _('RMA repair spare parts'),
            'move_ids': [(0, 0, {
                'name': _('RMA spare parts'),
                'company_id': quant.company_id.id,
                'product_id': quant.product_id.id,
                'product_uom': quant.product_id.uom_id.id,
                'product_uom_qty': qty_to_take,
                'location_id': quant.location_id.id,
                'location_dest_id': dest_location.id,
            })],
        })
        picking.action_confirm()
        picking.action_assign()
        for ml in picking.move_ids.move_line_ids:
            ml.lot_id = quant.lot_id
            ml.owner_id = quant.owner_id
            ml.package_id = quant.package_id
            ml.quantity = qty_to_take
        picking.move_ids.picked = True
        res = picking.with_context(skip_backorder=True).button_validate()
        if res is not True:
            raise UserError(
                _('The stock transfer could not be validated automatically. Complete the internal transfer manually.')
            )

        dom = [
            ('product_id', '=', quant.product_id.id),
            ('location_id', '=', dest_location.id),
            ('quantity', '>', 0),
        ]
        if quant.lot_id:
            dom.append(('lot_id', '=', quant.lot_id.id))
        else:
            dom.append(('lot_id', '=', False))
        if quant.owner_id:
            dom.append(('owner_id', '=', quant.owner_id.id))
        else:
            dom.append(('owner_id', '=', False))
        if quant.package_id:
            dom.append(('package_id', '=', quant.package_id.id))
        else:
            dom.append(('package_id', '=', False))

        dest_quants = self.env['stock.quant'].search(dom, order='id desc')
        match = dest_quants.filtered(
            lambda q: float_compare(q.quantity, qty_to_take, precision_rounding=q.product_uom_id.rounding) == 0
        )[:1]
        if match:
            return match
        if dest_quants:
            return dest_quants[0]
        return self.env['stock.quant']
