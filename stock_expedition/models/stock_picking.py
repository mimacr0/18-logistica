# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2025 DaFe Solutions
#
##############################################################################

from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    transport_insurance = fields.Boolean(string='Transport Insurance', related='sale_id.transport_insurance', store=True,  readonly=True,  help='If checked, transport insurance will be applied to this shipment.')
    allowed_partner_ids = fields.Many2many(comodel_name='res.partner', string='Direcciones de envío permitidas', compute='_compute_allowed_partner_ids',)

    @api.depends('picking_type_id')
    def _compute_allowed_partner_ids(self):
        """Filtra solo direcciones de envío si está configurado en el tipo de operación."""
        for picking in self:
            if picking.picking_type_id.use_delivery_address_domain:
                delivery_addresses = self.env['res.partner'].search([('type', '=', 'delivery')])
                picking.allowed_partner_ids = [(6, 0, delivery_addresses.ids)]
            else:
                picking.allowed_partner_ids = False

