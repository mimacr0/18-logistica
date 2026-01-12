# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2025 DaFe Solutions
#
##############################################################################

from odoo import models, fields


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    use_custom_partner_domain = fields.Boolean(
        string='Dominio personalizado de contactos',
        default=False,
        help='Si está activado, en los pickings de este tipo solo se podrán '
             'seleccionar empresas o contactos de empresas, excluyendo empleados.'
    )

    allowed_location_ids = fields.Many2many(
        comodel_name='stock.location',
        relation='stock_picking_type_allowed_src_location_rel',
        column1='picking_type_id',
        column2='location_id',
        string='Ubicaciones origen permitidas',
        help='Si se configuran, solo estas ubicaciones estarán disponibles como origen en los pickings de este tipo.'
    )

    allowed_location_dest_ids = fields.Many2many(
        comodel_name='stock.location',
        relation='stock_picking_type_allowed_dest_location_rel',
        column1='picking_type_id',
        column2='location_id',
        string='Ubicaciones destino permitidas',
        help='Si se configuran, solo estas ubicaciones estarán disponibles como destino en los pickings de este tipo.'
    )
