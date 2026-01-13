##############################################################################
#
# Copyright 2025 DaFe Solutions
#
##############################################################################

from markupsafe import Markup
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from .choices import MAINTENANCE_TYPE, LIFECYCLE_STATE


class QualityAlert(models.Model):
    _inherit = 'quality.alert'

    allowed_lot_ids = fields.Many2many('stock.lot', string='Lotes permitidos', compute='_compute_allowed_lot_ids')
    lot_id = fields.Many2one('stock.lot', 'Lot', check_company=True, domain="[('id', 'in', allowed_lot_ids)]")
    repair_order_ids = fields.One2many(comodel_name='repair.order', inverse_name='repair_alert_id', string='Linked Repair Orders')
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
        # Guardar producto anterior para detectar cambios
        old_products = {alert.id: alert.product_id for alert in self}
        
        # Detectar cambios antes del write
        picking_fields_changed = any(f in vals for f in ('lot_id', 'product_id', 'quantity'))
        
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

            # Si cambió producto, lote o cantidad, actualizar en los pickings
            if picking_fields_changed and alert.picking_ids:
                old_product = old_products.get(alert.id)
                alert._update_picking_lines(old_product)

        return res

    def _update_picking_lines(self, old_product=None):
        """Actualiza el producto, lote y cantidad en los pickings relacionados si son editables."""
        self.ensure_one()

        if not self.picking_ids:
            return

        # Verificar si hay pickings no editables (done o cancelled)
        non_editable_pickings = self.picking_ids.filtered(lambda p: p.state in ('done', 'cancel'))
        
        if non_editable_pickings:
            raise ValidationError(_(
                'No se puede modificar porque hay pickings en estado finalizado o cancelado: %s'
            ) % ', '.join(non_editable_pickings.mapped('name')))

        # Producto a buscar en las líneas (el anterior si cambió, o el actual)
        search_product = old_product if old_product else self.product_id

        for picking in self.picking_ids:
            # Buscar moves del producto
            moves = picking.move_ids.filtered(lambda m: m.product_id == search_product)
            
            if moves:
                # Actualizar stock.move
                move_vals = {
                    'product_id': self.product_id.id,
                    'product_uom_qty': self.quantity or 1,
                    'name': self.product_id.display_name,
                }
                moves.write(move_vals)
                
                # Actualizar stock.move.line
                for move in moves:
                    move_lines = move.move_line_ids
                    if move_lines:
                        line_vals = {
                            'product_id': self.product_id.id,
                            'quantity': self.quantity or 1,
                        }
                        if self.lot_id:
                            line_vals['lot_id'] = self.lot_id.id
                        move_lines.write(line_vals)
        
    def toggle_lock(self):
        """ Alterna el valor de is_locked """
        for record in self:
            record.is_locked = not record.is_locked

    def action_cancel(self):
        """Cancelar la alerta de calidad. Abre wizard si hay pickings completados o reparaciones."""
        self.ensure_one()
        
        # Verificar si hay pickings completados o reparaciones
        has_done_pickings = bool(self.picking_ids.filtered(lambda p: p.state == 'done'))
        has_repairs = bool(self.repair_order_ids)
        
        if has_done_pickings or has_repairs:
            # Abrir wizard para pedir motivo
            return {
                'name': _('Cancelar Alerta de Calidad'),
                'type': 'ir.actions.act_window',
                'res_model': 'quality.alert.cancel.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_alert_id': self.id,
                },
            }
        else:
            # Cancelar directamente sin motivo
            self._do_cancel()
            return True

    def _do_cancel(self, reason=None):
        """Ejecuta la cancelación de la alerta y sus elementos relacionados."""
        self.ensure_one()
        
        cancelled_stage = self.env.ref('repair_module.quality_alert_stage_repair_cancelled', raise_if_not_found=False)
        
        # Cancelar pickings no completados
        pickings_to_cancel = self.picking_ids.filtered(lambda p: p.state not in ('done', 'cancel'))
        if pickings_to_cancel:
            pickings_to_cancel.action_cancel()
        
        # Crear movimiento de retorno SOLO si hay pickings completados (producto ya movido a Repairs)
        done_pickings = self.picking_ids.filtered(lambda p: p.state == 'done')
        if done_pickings:
            self._create_return_from_repair_picking()
        
        # Cancelar reparaciones asociadas
        if self.repair_order_ids:
            repairs_to_cancel = self.repair_order_ids.filtered(lambda r: r.state != 'cancel')
            if repairs_to_cancel:
                repairs_to_cancel.action_repair_cancel()
        
        # Cambiar stage a cancelado
        if cancelled_stage:
            self.write({'stage_id': cancelled_stage.id})
        
        # Publicar motivo en el chatter si se proporcionó
        if reason:
            body = Markup('<strong>%s</strong><br/>%s: %s') % (
                _('Alerta cancelada'),
                _('Motivo'),
                reason
            )
            self.message_post(
                body=body,
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )
        else:
            self.message_post(
                body=Markup('<strong>%s</strong>') % _('Alerta cancelada'),
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )

    def _create_return_from_repair_picking(self):
        """Crea un picking de retorno para devolver productos desde ubicaciones de reparación a Stock."""
        self.ensure_one()
        
        return_picking_type = self.env.ref('repair_module.stock_picking_type_return_from_repair', raise_if_not_found=False)
        if not return_picking_type:
            return False
        
        stock_location = self.env.ref('stock.stock_location_stock', raise_if_not_found=False)
        if not stock_location:
            return False
        
        # Ubicaciones relacionadas con reparaciones
        repairs_location = self.env.ref('repair_module.stock_location_repairs', raise_if_not_found=False)
        to_relocate_location = self.env.ref('repair_module.stock_location_to_relocate', raise_if_not_found=False)
        
        repair_location_ids = []
        if repairs_location:
            repair_location_ids.append(repairs_location.id)
        if to_relocate_location:
            repair_location_ids.append(to_relocate_location.id)
        
        if not repair_location_ids:
            return False
        
        # Buscar quants solo en ubicaciones de reparación
        domain = [
            ('product_id', '=', self.product_id.id),
            ('location_id', 'in', repair_location_ids),
            ('quantity', '>', 0),
        ]
        if self.lot_id:
            domain.append(('lot_id', '=', self.lot_id.id))
        
        quants = self.env['stock.quant'].search(domain)
        
        if not quants:
            return False
        
        # Usar la cantidad de la alerta, no toda la cantidad del quant
        quantity_to_return = self.quantity or 1
        
        # Tomar el primer quant con stock (priorizar Repairs sobre Stock a reubicar)
        quant = quants.filtered(lambda q: q.location_id == repairs_location)[:1] or quants[:1]
        
        move_lines_data = [{
            'product_id': quant.product_id.id,
            'quantity': min(quantity_to_return, quant.quantity),
            'lot_id': quant.lot_id.id if quant.lot_id else False,
            'location_src_id': quant.location_id.id,
            'location_dest_id': stock_location.id,
        }]
        
        # Usar las ubicaciones del primer movimiento para la cabecera del picking
        first_line = move_lines_data[0]
        
        # Crear el picking de retorno
        picking_vals = {
            'partner_id': self.partner_id.id if self.partner_id else False,
            'origin': _('Cancellation %s') % self.name,
            'picking_type_id': return_picking_type.id,
            'location_id': first_line['location_src_id'],
            'location_dest_id': first_line['location_dest_id'],
            'quality_alert_ids': [(4, self.id)],
        }
        # Añadir campo opcional si existe
        if 'account_partner_id' in self.env['stock.picking']._fields:
            picking_vals['account_partner_id'] = self.account_partner_id.id if self.account_partner_id else False
        
        return_picking = self.env['stock.picking'].create(picking_vals)
        
        # Crear los movimientos
        for line_data in move_lines_data:
            product = self.env['product.product'].browse(line_data['product_id'])
            move_vals = {
                'name': product.display_name,
                'product_id': product.id,
                'product_uom_qty': line_data['quantity'],
                'product_uom': product.uom_id.id,
                'picking_id': return_picking.id,
                'location_id': line_data['location_src_id'],
                'location_dest_id': line_data['location_dest_id'],
            }
            move = self.env['stock.move'].create(move_vals)
            
            # Crear move line
            move_line_vals = {
                'move_id': move.id,
                'picking_id': return_picking.id,
                'product_id': product.id,
                'quantity': line_data['quantity'],
                'location_id': line_data['location_src_id'],
                'location_dest_id': line_data['location_dest_id'],
            }
            if line_data['lot_id']:
                move_line_vals['lot_id'] = line_data['lot_id']
            
            self.env['stock.move.line'].create(move_line_vals)
        
        # Confirmar el picking para reservar
        return_picking.action_confirm()
        
        return return_picking

    def _set_default_stage(self):
        self.ensure_one()
        default_stage = self.env.ref('repair_module.quality_alert_stage_received', raise_if_not_found=False)
        if default_stage:
            self.write({
                'stage_id': default_stage.id
            })

    @api.depends('product_id')
    def _compute_allowed_lot_ids(self):
        """Filtra lotes disponibles: en ubicaciones internas y con stock no reservado."""
        for alert in self:
            if not alert.product_id:
                alert.allowed_lot_ids = False
                continue

            # Buscar quants del producto en ubicaciones internas con cantidad disponible
            quants = self.env['stock.quant'].search([
                ('product_id', '=', alert.product_id.id),
                ('location_id.usage', '=', 'internal'),
                ('quantity', '>', 0),
            ])

            # Filtrar quants con cantidad realmente disponible (no reservada)
            available_quants = quants.filtered(lambda q: (q.quantity - q.reserved_quantity) > 0)

            # Obtener los lotes únicos de esos quants
            lot_ids = available_quants.mapped('lot_id').ids
            alert.allowed_lot_ids = [(6, 0, lot_ids)] if lot_ids else False

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

        # Validar account_partner solo si el campo existe
        if 'account_partner_id' in self._fields and not self.account_partner_id:
            raise ValidationError(_('An account partner must be selected.'))

        # Validación de lot solo si el producto es serial/lot
        if self.product_id.tracking in ['serial', 'lot'] and not self.lot_id:
            raise ValidationError(_('A lot/serial must be selected for this product.'))

        picking_type = self.env.ref('repair_module.stock_picking_type_move_to_repair')
        total_qty_to_move = self.quantity
        
        picking_vals = {
            'partner_id': self.partner_id.id if self.partner_id else False,
            'origin': self.name,
            'picking_type_id': picking_type.id,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': picking_type.default_location_dest_id.id,
            'quality_alert_ids': [(6, 0, [self.id])],
        }
        # Añadir campos opcionales si existen en el modelo
        if 'account_partner_id' in self.env['stock.picking']._fields:
            picking_vals['account_partner_id'] = self.account_partner_id.id if self.account_partner_id else False
        if 'maintenance_type' in self.env['stock.picking']._fields:
            picking_vals['maintenance_type'] = self.maintenance_type
        
        picking = self.env['stock.picking'].create(picking_vals)
    
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


