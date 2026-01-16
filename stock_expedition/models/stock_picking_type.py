# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2025 DaFe Solutions
#
##############################################################################

from odoo import models, fields


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    use_delivery_address_domain = fields.Boolean(
        string='Solo direcciones de envío',
        default=False,
        help='Si está activado, en los pickings de este tipo solo se podrán '
             'seleccionar direcciones de envío (type=delivery).'
    )
