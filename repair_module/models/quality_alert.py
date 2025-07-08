##############################################################################
#
# Copyright 2025 DaFe Solutions
#
##############################################################################

from odoo import models, fields, api, _


class QualityAlert(models.Model):
    _inherit = 'quality.alert'

    repair_order_id = fields.Many2one('repair.order', string='Associated Technical Order')
    account_partner_id = fields.Many2one(string='Owner Account', comodel_name='account.partner')
    quantity = fields.Integer(string='Quantity')
    stock_picking_count = fields.Integer(compute='_compute_stock_picking_count')
    check_ids = fields.Many2one('quality.check', string='Quality Checks')
    picking_ids = fields.Many2many('stock.picking', 'quality_alert_picking_rel', string='Pickings', check_company=True)

    """
        Tengo que concretar los estados (quality.alert.stage), por defecto, quality crea 4 que son Nuevo, Confirmado, Acción propuesta y Resuelto
        Habría que añadir:
        - En transito (recepción): para cuando el cliente crea una recepción y crea/creamos la alerta 
        - En el almacén: validamos la recepción (no he puesto recibido, porque lo he usado más adelante) 
        - Revisión preliminar: cuando confirmamos que todo está bien con la cantidad
        Viendo esto ahora, tengo la sensación de que revisión preliminar, es una revisión normal que tiene que hacer el departamento de reparación (confirmar con el responsable)
        - Enviado a revisar: si el cliente necesita una revisión antes de tomar una decisión sobre lo que se puede hacer con el producto
        - Enviado a reparar: si el cliente confirma que quiere repararlo
        - Enviado a postventa: cuando se devuelve a postventa, esto puede ser tanto tras una revisión como tras una reparación
        - Enviado a reciclar: si el cliente considera que o se puede reparar ni renovar
        - En transito (Expedición): si la reparacón / renovación ha ido bien y el producto puede ser devuelto al cliente
        - Enviado: Cuando el transportista se lo lleve
        - Recibido: si el usuario del aparato que ha enviado el movil ha recibido el aparato

        Cree el data, pero hay que revisarlo.
        Tampoco se muy bien si es correcto usar quality alert
    """ 
    
    @api.depends('picking_ids')
    def _compute_picking_id(self):
        for record in self:
            record.picking_id = record.picking_ids[:1] if record.picking_ids else False

    def _compute_stock_picking_count(self):
        for picking in self:
            picking.stock_picking_count = len(self.picking_id)

    @api.onchange('account_partner_id')
    def _set_partner_and_owner(self):
        for sale in self:
            if sale.account_partner_id and sale.account_partner_id.partner_id:
                sale.partner_id = sale.account_partner_id.partner_id
            else:
                sale.partner_id = False

    def action_create_move_to_repair(self):
        self.ensure_one()
        self.stage_id = self.env.ref('quality.quality_alert_stage_1')
        # Cargar la vista de formulario de stock.picking
        picking_form_view = self.env.ref('stock.view_picking_form')
        picking_type = self.env.ref('repair_module.stock_picking_type_move_to_repair')

        return {
            'type': 'ir.actions.act_window',
            'name': _('Crear Movimiento de Reparación'),
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'target': 'current',
            'views': [(picking_form_view.id, 'form')],
            'context': {
                'default_account_partner_id': self.account_partner_id.id,
                'default_origin': self.name,
                'default_partner_id': self.partner_id.id,
                'default_picking_type_id': picking_type.id,  # Permite elegir el tipo
                'default_quality_alert_ids': [(6, 0, [self.id])],
                # 'default_location_id': self.location_id.id if self.location_id else False,
                # 'default_location_dest_id': self.location_dest_id.id if self.location_dest_id else False,
                'default_move_ids_without_package': [
                    (0, 0, {
                        'name': self.product_id.display_name or '',
                        'product_id': self.product_id.id,
                        'product_uom_qty': self.quantity,
                        'lot_ids': [(6, 0, [self.lot_id.id])] if self.lot_id else False,
                        'quantity': 1 if self.lot_id else 0,
                        # 'location_id': self.location_id.id if self.location_id else False,
                        # 'location_dest_id': self.location_dest_id.id if self.location_dest_id else False,
                    })
                ],
            },
        }

        
    def open_stock_picking(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id('stock.stock_picking_action_picking_type')

        related_pickings = self.picking_id  # Asegúrate de que este campo exista

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


