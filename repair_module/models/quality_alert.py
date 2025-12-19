##############################################################################
#
# Copyright 2025 DaFe Solutions
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from .choices import MAINTENANCE_TYPE, LIFECYCLE_STATE


class QualityAlert(models.Model):
    _inherit = 'quality.alert'

    repair_order_ids = fields.One2many(comodel_name='repair.order', inverse_name='repair_alert_id', string='Órdenes de reparación vinculadas')
    account_partner_id = fields.Many2one(string='Owner Account', comodel_name='account.partner')
    maintenance_type = fields.Selection(MAINTENANCE_TYPE, string='Maintenance Type')
    quantity = fields.Integer(string='Quantity')
    stock_picking_count = fields.Integer(compute='_compute_stock_picking_count')
    check_ids = fields.Many2one('quality.check', string='Quality Checks')
    picking_ids = fields.Many2many(
        'stock.picking',
        'quality_alert_picking_rel',
        column1='quality_alert_id',
        column2='stock_picking_id',
        string='Pickings',
        check_company=True
    )
    schedule_date = fields.Date(string="Schedule Date")
    is_repair = fields.Boolean(string='Is Repair', default=False)
    is_locked = fields.Boolean(default=True)
    
    # Override user_id to remove default (domain set in view to filter by After Sales group)
    user_id = fields.Many2one(
        'res.users',
        string='Responsible',
        tracking=True,
        default=False,  # Remove default (base model sets self.env.user)
        help='Responsible user. Only users from After Sales Department can be assigned. Defaults to team leader if not specified.'
    )
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override para asignar stage y leader como responsable al crear un nuevo alert"""
        records = super().create(vals_list)
        for record in records:
            record._set_default_stage()
            # Asignar el leader del equipo como responsable si no se especificó user_id
            if not record.user_id and record.team_id and record.team_id.leader_id:
                record.user_id = record.team_id.leader_id
        return records

    def write(self, vals):
        for alert in self:
            messages = []

            # Detectar cambio de bloqueo
            if 'is_locked' in vals and vals['is_locked'] != alert.is_locked:
                state = 'locked' if vals['is_locked'] else 'unlocked'
                messages.append(_("Alert has been %s by %s") % (state, self.env.user.name))

            # Detectar cambio de etapa
            if 'stage_id' in vals and vals['stage_id'] != alert.stage_id.id:
                new_stage = self.env['quality.alert.stage'].browse(vals['stage_id']).name
                messages.append(_("Stage changed to '%s' by %s") % (new_stage, self.env.user.name))

            # Llamar al super write primero
            res = super(QualityAlert, alert).write(vals)

            # Publicar mensajes en el chatter
            for msg in messages:
                alert.message_post(body=msg)

        return res
        
    def toggle_lock(self):
        """ Alterna el valor de is_locked """
        for record in self:
            record.is_locked = not record.is_locked

    def _set_default_stage(self):
        self.ensure_one()
        default_stage = self.env.ref('repair_module.quality_alert_stage_received', raise_if_not_found=False)
        if default_stage:
            self.write({
                'stage_id': default_stage.id
            })

    @api.depends('picking_ids')
    def _compute_picking_id(self):
        for record in self:
            record.picking_id = record.picking_ids[:1] if record.picking_ids else False

    def _compute_stock_picking_count(self):
        for picking in self:
            picking.stock_picking_count = len(self.picking_ids)

    @api.onchange('account_partner_id')
    def _set_partner_and_owner(self):
        for sale in self:
            if sale.account_partner_id and sale.account_partner_id.partner_id:
                sale.partner_id = sale.account_partner_id.partner_id
            else:
                sale.partner_id = False

    def action_create_move_to_repair(self, location_id=None):
        self.ensure_one()
        
        if self.quantity <= 0:
            raise ValidationError(_('Quantity must be greater than 0.'))

        if not self.product_id:
            raise ValidationError(_('A product must be selected.'))

        # Validación de lot solo si el producto es serial/lot
        if self.product_id.tracking in ['serial', 'lot'] and not self.lot_id:
            raise ValidationError(_('A lot/serial must be selected for this product.'))

        picking_type = self.env.ref('repair_module.stock_picking_type_move_to_repair')
        total_qty_to_move = self.quantity
        
        picking = self.env['stock.picking'].create({
            'account_partner_id': self.account_partner_id.id,
            'partner_id': self.partner_id.id if self.partner_id else False,
            'origin': self.name,
            'picking_type_id': picking_type.id,
            'location_id': picking_type.default_location_src_id.id,  # From picking type configuration
            'location_dest_id': picking_type.default_location_dest_id.id,
            'quality_alert_ids': [(6, 0, [self.id])],
            'maintenance_type': self.maintenance_type,
        })
    
        quants = self._get_quants_for_move(location_id=location_id)
        for quant in quants:
            available_qty = quant.quantity - quant.reserved_quantity
            if available_qty <= 0:
                continue

            qty_to_move = min(total_qty_to_move, available_qty)

            move_vals = {
                'name': quant.product_id.display_name,
                'product_id': quant.product_id.id,
                'product_uom_qty': qty_to_move,
                'product_uom': quant.product_id.uom_id.id,
                'picking_id': picking.id,
                'location_id': quant.location_id.id,
                'location_dest_id': picking_type.default_location_dest_id.id,
            }
            move = self.env['stock.move'].create(move_vals)

            # Reserve the lot without qty_done - operator will scan from PDA to confirm
            move_line_vals = {
                'move_id': move.id,
                'picking_id': picking.id,  # Explicit picking_id for stock_barcode module
                'product_id': quant.product_id.id,
                'quantity': qty_to_move,  # Reserved quantity
                'location_id': quant.location_id.id,
                'location_dest_id': picking_type.default_location_dest_id.id,
                **({'lot_id': quant.lot_id.id} if quant.lot_id else {}),
            }
            self.env['stock.move.line'].create(move_line_vals)

            total_qty_to_move -= qty_to_move
            if total_qty_to_move <= 0:
                break

        if total_qty_to_move > 0:
            raise ValidationError(_('Not enough quantity available. Remaining: %s') % total_qty_to_move)

        # Confirm the picking to reserve the stock
        picking.action_confirm()

        self.write({'picking_ids': [(4, picking.id)]})

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id': picking.id,
            'target': 'current',
        }
    def _get_quants_for_move(self, location_id=None):
        """
        Devuelve los quants disponibles para crear el stock.move.
        - Si el producto tiene tracking serial/lot, usa self.lot_id.quant_ids
        - Si no tiene tracking, filtra por location_id si se pasa, o toma todos los quants disponibles
        """
        self.ensure_one()
        
        if self.product_id.tracking in ['serial', 'lot']:
            quants = self.lot_id.quant_ids
            # Filtrar quants con cantidad positiva
            quants = quants.filtered(lambda q: (q.quantity - q.reserved_quantity) > 0)
            return quants
        else:
            domain = [('product_id', '=', self.product_id.id)]
            if location_id:
                domain.append(('location_id', '=', int(location_id)))

            quants = self.env['stock.quant'].search(domain)
            # Filtrar cantidad realmente disponible (restando reserved_quantity)
            quants = quants.filtered(lambda q: (q.quantity - q.reserved_quantity) > 0)
            return quants
            
    def open_stock_picking(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id('stock.stock_picking_action_picking_type')

        related_pickings = self.picking_ids  # Asegúrate de que este campo exista

        action.update({
            'domain': [('id', 'in', related_pickings.ids)],
            'context': {
                'default_quality_alert_ids': [(4, self.id)],
            },
            'views': [(False, 'list'), (False, 'form')],
        })

        if len(related_pickings) == 1:
            action['views'] = [(False, 'form')]
            action['res_id'] = related_pickings.id

        return action


