from odoo import models, fields, api, _
from .choices import MAINTENANCE_TYPE, LIFECYCLE_STATE
from odoo.exceptions import ValidationError
from odoo.tools import float_compare, float_is_zero, clean_context

class RepairOrder(models.Model):
    _inherit = 'repair.order'

    account_partner_id = fields.Many2one(string='Owner Account', comodel_name='account.partner')
    origin = fields.Char(string='Origin')
    repair_alert_id = fields.Many2one( comodel_name='quality.alert', string='Alerta de Calidad', help='Alerta de calidad que generó este movimiento.')
    description = fields.Html(string="Problem Description")
    diagnosis_ids = fields.Many2many(comodel_name='repair.diagnosis', string='Diagnosis', relation='repair_order_repair_diagnosis_rel', column1='repair_id', column2='diagnosis_id')
    result_ids = fields.Many2many(comodel_name='repair.result', string='Results', relation='repair_order_repair_result_rel', column1='repair_id', column2='result_id')
    technician_id = fields.Many2one(
        comodel_name="res.users",
        string="Technician",
        domain=lambda self: [('groups_id', 'in', [self.env.ref('logistics_security.group_repair_user').id])]
    )    
    maintenance_type = fields.Selection(MAINTENANCE_TYPE, string='Maintenance Type')
    lifecycle_state = fields.Selection(LIFECYCLE_STATE, string='Lifecycle State')
    confirm_date = fields.Datetime(string='Confirm Date')
    assigned_date = fields.Datetime(string='Assigned Date')
    assigned_user_id = fields.Many2one('res.users', string='Assigned User')
    in_progress_date = fields.Datetime(string='In Progress Date')
    in_progress_user_id = fields.Many2one('res.users', string='In Progress User')
    done_date = fields.Datetime(string='Done Date')
    done_user_id = fields.Many2one('res.users', string='Done User')
    
    @api.onchange('account_partner_id')
    def _set_partner_and_owner(self):
        for sale in self:
            if sale.account_partner_id and sale.account_partner_id.partner_id:
                sale.partner_id = sale.account_partner_id.partner_id
            else:
                sale.partner_id = False


    ## Allows to assign the account_partner_id to the new sale.order
    def action_create_sale_order(self):
        res = super().action_create_sale_order()
        sale_orders = self.mapped('sale_order_id')
        for repair in self:
            if repair.sale_order_id and repair.account_partner_id:
                repair.sale_order_id.account_partner_id = repair.account_partner_id
        return res

    def button_set_technician(self):
        return {
            'name': _('Set Technician'),
            'type': 'ir.actions.act_window',
            'res_model': 'repair.technician.set',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_repair_id': self.id,
                'default_technician_id': self.technician_id.id,
            },
        }

    def action_validate(self):
        if not self.technician_id:
            raise ValidationError(_('Please assign a technitian first'))

        res = super().action_validate()
        # actualizar campos en el propio repair.order
        self.write({
            'confirm_date': fields.Datetime.now(),
            'assigned_date': fields.Datetime.now(),
            'assigned_user_id': self.env.user.id,
        })

        # Registrar en el chatter a quién se asignó
        self.message_post(
            body=_("Repair assigned to technician: %s") % self.technician_id.name,
            message_type='notification',
        )

        return res

    def create(self, vals):
        res = super().create(vals) 
        if self.repair_alert_id:
            res.repair_alert_id.stage_id = self.env.ref('quality.quality_alert_stage_2')
        return res

    def action_repair_start(self):
        res = super().action_repair_start()
        if self.repair_alert_id:
            self.repair_alert_id.stage_id = self.env.ref('repair_module.quality_alert_stage_repairing')
        
        self.write({
            'in_progress_date': fields.Datetime.now(),
            'in_progress_user_id': self.env.user.id,
        })
        
        return res

    def action_repair_end(self):
        self.ensure_one()
        if not self.lifecycle_state and self.product_id.tracking == 'serial':
            raise ValidationError(_('Please assign a new lifecycle state'))

        res = super().action_repair_end()
        if self.repair_alert_id:
            self.repair_alert_id.stage_id = self.env.ref('repair_module.quality_alert_stage_sent_to_postsale')
        
        # Marcar quién y cuándo terminó la reparación
        self.write({
            'done_date': fields.Datetime.now(),
            'done_user_id': self.env.user.id,
        })

        if self.lot_id:
            self.lot_id.diagnosis_ids = [(6, 0, self.diagnosis_ids.ids)]
            self.lot_id.result_ids = [(6, 0, self.result_ids.ids)]
            self.lot_id.lifecycle_state = self.lifecycle_state

        return res  



    def action_repair_done(self):
        """Completa la reparación, creando un picking interno y moves para el producto final."""
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        product_move_vals = []
        # Cancelar moves con cantidad 0
        self.move_ids.filtered(
            lambda m: float_is_zero(m.quantity, precision_rounding=m.product_uom.rounding)
        )._action_cancel()

        no_service_policy = 'service_policy' not in self.env['product.template']

        for repair in self:
            if all(not move.picked for move in repair.move_ids):
                repair.move_ids.picked = True

            if repair.sale_order_line_id:
                ro_origin_product = repair.sale_order_line_id.product_template_id
                if ro_origin_product.type == 'service' and (
                    no_service_policy or ro_origin_product.service_policy == 'ordered_prepaid'
                ):
                    repair.sale_order_line_id.qty_delivered = repair.sale_order_line_id.product_uom_qty

            if not repair.product_id:
                continue

            if repair.product_id.product_tmpl_id.tracking != 'none' and not repair.lot_id:
                raise ValidationError(_(
                    "Serial number is required for product to repair : %s",
                    repair.product_id.display_name
                ))

        location_src = self.env.ref('repair_module.stock_location_repairs', raise_if_not_found=False)
        location_dest = self.env.ref('repair_module.stock_location_to_relocate', raise_if_not_found=False)

        if not location_src or not location_dest:
            raise ValidationError(_("No se encontraron las ubicaciones 'Repairs' o 'Stock a reubicar'. Actualiza el módulo repair_module."))

        # --- Crear el Picking (transferencia interna) ---
        picking_type = self.env.ref('repair_module.stock_picking_type_return_from_repair', raise_if_not_found=False)
        if not picking_type:
            raise ValidationError(_("No se encontró el tipo de operación 'Return from Repair'. Actualiza el módulo repair_module."))
        
        picking_vals = {
            'account_partner_id': self.account_partner_id.id,
            'partner_id': self[:1].partner_id.id if self[:1].partner_id else False,
            'origin': ', '.join(self.mapped('name')),
            'picking_type_id': picking_type.id,
            'location_id': location_src.id,
            'location_dest_id': location_dest.id,
        }
        picking = self.env['stock.picking'].create(picking_vals)

        # --- Crear Moves asociados al Picking ---
        for repair in self:
            owner_id = False
            available_qty_owner = self.env['stock.quant']._get_available_quantity(
                repair.product_id,
                repair.product_location_src_id,
                repair.lot_id,
                owner_id=repair.partner_id,
                strict=True
            )
            if float_compare(available_qty_owner, repair.product_qty, precision_digits=precision) >= 0:
                owner_id = repair.partner_id.id

            product_move_vals.append({
                'name': repair.name,
                'product_id': repair.product_id.id,
                'product_uom_qty': repair.product_qty,
                'product_uom': repair.product_uom.id or repair.product_id.uom_id.id,
                'location_id': location_src.id,
                'location_dest_id': location_dest.id,
                'picking_id': picking.id,
                'repair_id': repair.id,
                'move_line_ids': [(0, 0, {
                    'product_id': repair.product_id.id,
                    'lot_id': repair.lot_id.id,
                    'product_uom_id': repair.product_uom.id or repair.product_id.uom_id.id,
                    'quantity': repair.product_qty,
                    'owner_id': owner_id,
                    'location_id': location_src.id,
                    'location_dest_id': location_dest.id,
                })],
            })

        product_moves = self.env['stock.move'].create(product_move_vals)

        if self.repair_alert_id:
            self.repair_alert_id.write({'picking_ids': [(4, picking.id)]})

            # (Opcional) mensaje en el chatter del alert
            self.repair_alert_id.message_post(
                body=_("Se ha creado una transferencia interna <a href=# data-oe-model='stock.picking' data-oe-id='%d'>%s</a> desde NV1P2S7 hacia NV1P2S4R.")
                % (picking.id, picking.name)
                )

        # Asignar el move principal a la reparación
        repair_move = {m.repair_id.id: m for m in product_moves}
        for repair in self:
            move_id = repair_move.get(repair.id, False)
            if move_id:
                repair.move_id = move_id

        # Actualizar estado de reparación
        self.state = 'done'

        # Actualizar líneas de venta si existen
        for sale_line in self.move_ids.sale_line_id:
            price_unit = sale_line.price_unit
            sale_line.write({'product_uom_qty': sale_line.qty_delivered, 'price_unit': price_unit})
        return True

    # def open_quality_check(self):
    #     self.ensure_one()
    #     action = self.env['ir.actions.actions']._for_xml_id('quality_control.quality_check_action_team')

    #     related_quality_check = self.quality_check_id  # Asegúrate de que este campo exista

    #     action.update({
    #         'domain': [('id', 'in', related_quality_check.ids)],
    #         'context': {
    #             'default_quality_alert_ids': [(4, self.id)],
    #             'default_repair_alert_id': record.repair_alert_id.id,
    #         },
    #         'views': [(False, 'list'), (False, 'form')],
    #     })

    #     if len(related_quality_check) == 1:
    #         action['views'] = [(False, 'form')]
    #         action['res_id'] = related_quality_check.id

    #     return action

