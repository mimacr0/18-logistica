##############################################################################
#
# Copyright 2026 DaFe Solutions
#
##############################################################################

from odoo import models, fields, api, _
from odoo.tools import html2plaintext
from odoo.exceptions import UserError
import json
from markupsafe import Markup
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    _description = 'Sale order generalized'
    _order = 'name desc'

    # --- CAMPOS DE IDENTIFICACIÓN Y ORIGEN ---
    
    # [COMENTARIO]: account_id parece ser una referencia a un partner específico o cuenta contable.
    # Si es para agrupar pedidos por "cuenta de cliente", está bien aquí.
    account_id = fields.Many2one('account.partner', string='Account')
    
    sender_id = fields.Many2one(
        comodel_name='res.partner',
        string="Sender",
        compute='_compute_partner_sender_id',
        store=True, readonly=False, precompute=True,
        check_company=True,
        index='btree_not_null')

    # --- CAMPOS DE LOGÍSTICA (TRANSPORTE Y PAQUETERÍA) ---
    # [COMENTARIO]: Estos campos suelen estar mejor en el Albarán (stock.picking) o en el Paquete (stock.quant.package)
    # ya que un Pedido de Venta puede tener múltiples envíos y diferentes pesos/bultos por envío.
    
    carrier_id = fields.Many2one('delivery.carrier', string='Carrier')
    delivery_type = fields.Selection(related='carrier_id.delivery_type', string='Delivery Type')
    
    shipping_lumps = fields.Integer('Shipping Lumps', default=1)
    shipping_package = fields.Selection([
        ('box', 'Box'), 
        ('pallet','Palet'), 
        ('envelope', 'Envelope')
    ], string='Shipping Package', default='box')
    
    total_weight = fields.Float(string='Weight Shipping')
    
    # --- CAMPOS DE ESTADO Y TRACKING ---
    # [COMENTARIO]: El tracking_ref y los estados de entrega son específicos de cada expedición. 
    # En Odoo estándar, estos viven en stock.picking. Ponerlo aquí asume 1 envío por pedido.
    
    carrier_tracking_ref = fields.Char(string='Tracking Reference', copy=False)
    date_shipped = fields.Date(string="Shipment Date", readonly=True)
    date_delivered = fields.Datetime(string="Date Delivery", readonly=True)
    
    tracking_state = fields.Char(readonly=True, index=True, tracking=True)
    tracking_state_history = fields.Text(readonly=True)
    
    delivery_state = fields.Selection(selection=[
            ("label_created", "Label created, not yet picked up"),
            ("shipping_recorded_in_carrier", "Shipping recorded in carrier"),
            ("in_transit", "In transit"),
            ("canceled_shipment", "Canceled shipment"),
            ("customer_delivered", "Customer delivered"),
            ("warehouse_delivered", "Warehouse delivered"),
            ("no_update", "No more updates from carrier"),
            ("pickup_scan", "Package picked up"),
            ("customs_clearance", "Customs clearance in progress"),
            ("pending_government_release", "Pending government agency release"),
            ("government_released", "Released by government agency"),
            ("arrived_facility", "Arrived at facility"),
            ("departed_facility", "Departed from facility"),
            ("incidence", "Incidence")
        ],
        string="Carrier State",
        tracking=True,
        readonly=True
    )
    
    state_carrier = fields.Selection(selection=[
        ('engraved', 'ENGRAVED'),
        ('in_transit', 'IN TRANSIT'),
        ('finalized', 'FINALIZED'),
        ('incidence', 'INCIDENCE'),
        ('canceled', 'CANCELED')
    ], string='State Carrier', compute='_compute_state_carrier', store=True)

    # --- ATRIBUTOS DE ARCHIVO Y OTROS ---
    label_file_id = fields.Many2one(comodel_name='ir.attachment', string='Label File', copy=False)
    label_attachment_ids = fields.Many2many(comodel_name='ir.attachment', string='Label')
    
    created_in_portal = fields.Boolean(compute="_compute_has_archived_products")
    is_external_sender = fields.Boolean(string='External Sender', compute='_compute_is_external_sender')
    observations = fields.Text(string='Observations', translate=True, size=100)

    # --- COMPUTES Y LOGICA DE NEGOCIO ---

    @api.depends('delivery_state', 'tracking_state')
    def _compute_state_carrier(self):
        for order in self:
            if order.delivery_state == 'incidence' and order.tracking_state and '[3000]' in order.tracking_state:
                order.state_carrier = 'canceled'
            elif order.delivery_state == 'shipping_recorded_in_carrier':
                order.state_carrier = 'engraved'
            elif order.delivery_state in ('in_transit', 'no_update'):
                order.state_carrier = 'in_transit'
            elif order.delivery_state in ('customer_delivered', 'warehouse_delivered'):
                order.state_carrier = 'finalized'
            elif order.delivery_state in ('incident', 'incidence'):
                order.state_carrier = 'incidence'
            elif order.delivery_state == 'canceled_shipment':
                order.state_carrier = 'canceled'
            else:
                order.state_carrier = False

    @api.depends('company_id', 'sender_id')
    def _compute_is_external_sender(self):
        for order in self:
            if order.sender_id and order.sender_id.country_id:
                order.is_external_sender = order.sender_id.country_id.id != order.company_id.partner_id.country_id.id
            else:
                order.is_external_sender = False

    @api.depends('order_line.product_id')
    def _compute_has_archived_products(self):
        for order in self:
            # has_archived_products no está definido arriba, supongo que es auxiliar o falta el campo.
            order.created_in_portal = any(product.default_code == 'PORTAL' for product in order.order_line.product_id)

    @api.onchange('account_id')
    def _onchange_account_id(self):
        for order in self:
            if order.account_id and order.account_id.partner_id:
                order.partner_id = order.account_id.partner_id.commercial_partner_id

    @api.depends('partner_id')
    def _compute_partner_sender_id(self):
        for order in self:
            if order.partner_id:
                order.sender_id = order.partner_id.commercial_partner_id.address_get(['sender'])['sender']
            else:
                order.sender_id = False

    # --- ACCIONES ---

    def action_print_label(self):
        self.ensure_one()
        if self.label_file_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Label'),
                    'message': _('Label already printed'),
                    'type': 'success'
                }
            }
        if self.carrier_id:
            self.carrier_id.send_so_shipping(self)
            self.get_portal_url()
        return True

    # --- OVERRIDES Y EXTENSIONES DE ODOO ---

    def action_confirm(self):
        result = super().action_confirm()
        orders = self.sudo() if self.env.context.get('from_portal') else self
        orders = orders.filtered(lambda o: o.state == 'sale')
        orders.create_shipping_label_after_confirm()
        orders.action_lock()
        if self.env.context.get('from_portal'):
            orders.send_message_form_confirm_portal()
        return result

    def create_shipping_label_after_confirm(self):
        for order in self:
            if order.carrier_id and not order.label_file_id:
                try:
                    order.carrier_id.send_so_shipping(order)
                    order.get_portal_url()
                    order.message_post(body=_("Shipping label automatically created upon order confirmation"))
                except Exception as e:
                    order.message_post(body=_("Failed to automatically create shipping label: %s") % str(e))

    def write(self, vals):
        res = super().write(vals)
        return res

    def _action_cancel(self):
        # Cancelamos el envío antes de cancelar el pedido
        self._action_cancel_shipment()
        return super()._action_cancel()

    def _action_cancel_shipment(self):
        for order in self.filtered('label_file_id'):
            try:
                order.carrier_id.cancel_so_shipping(order)
                order.message_post(body=_("Shipping label canceled"))
                if hasattr(order, '_remove_delivery_line'):
                    order._remove_delivery_line()
                order.write({ 
                    'state': 'draft', 
                    'label_file_id': False, 
                    'carrier_id': False 
                })
            except Exception as e:
                _logger.error("Error canceling shipment: %s", e)

    # --- UTILIDADES Y MENSAJERÍA ---

    def send_message_form_confirm_portal(self):
        for order in self:
            try:
                partner_lang = order.partner_id.lang or self.env.user.lang or 'en_US'
                order_lang = order.with_context(lang=partner_lang)
                
                formatted_amount = '{:.2f}'.format(order.amount_total or 0.0)
                package_info = ""
                if order.carrier_id and hasattr(order.carrier_id, 'shipping_package'):
                    package_info = f"<li style='padding: 5px 0;'><strong>{_('Package Type')}:</strong> {order.carrier_id.shipping_package}</li>"

                body_message = f"""
                <div style="font-family: Arial, sans-serif; color: #4a4a4a;">
                    <p>{_('Dear')} <strong>{order.partner_id.name}</strong>,</p>
                    <p>{_('Your order with number')} <strong>{order.name}</strong> {_('has been confirmed.')}</p>
                    <div style="background-color: #f9f9f9; padding: 15px; border-radius: 4px;">
                        <ul style="list-style-type: none; padding: 0;">
                            <li><strong>{_('Shipping Method')}:</strong> {order.carrier_id.name}</li>
                            {package_info}
                            <li><strong>{_('Total Amount')}:</strong> {formatted_amount} {order.currency_id.symbol}</li>
                        </ul>
                    </div>
                </div>
                """
                order.message_post(
                    body=Markup(body_message),
                    message_type='comment',
                    subtype_xmlid="mail.mt_comment"
                )
            except Exception as e:
                _logger.error("Error sending portal confirmation message: %s", e)