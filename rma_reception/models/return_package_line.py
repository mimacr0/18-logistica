# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2026 DaFe Solutions
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RmaPackageLine(models.Model):
    _name = 'rma.package.line'
    _description = 'Líneas de los Paquetes RMA'

    package_id = fields.Many2one('stock.quant.package', string='Paquete', ondelete='cascade')
    product_map_id = fields.Many2one('account.product.map', string='Producto de Cliente', required=True)
    quantity = fields.Integer(string='Cantidad', default=1)
    received_qty = fields.Integer(
        string='Cantidad recibida',
        default=1,
        help='Cantidad efectivamente recibida; al desempaquetar se crean tantas unidades RMA o tanto stock como indique este campo.',
    )
    unpacked = fields.Boolean(string='Unpacked', default=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'received_qty' not in vals:
                vals['received_qty'] = vals.get('quantity', 1)
        return super().create(vals_list)

    @api.onchange('quantity')
    def _onchange_quantity_set_received_qty(self):
        for line in self:
            line.received_qty = line.quantity

    @api.constrains('received_qty')
    def _check_received_qty_non_negative(self):
        for line in self:
            if line.received_qty < 0:
                raise ValidationError(_('La cantidad recibida no puede ser negativa.'))