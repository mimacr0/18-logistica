# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    rma_move_desk_root_location_ids = fields.Many2many(
        'stock.location',
        'res_company_rma_move_desk_root_loc_rel',
        'company_id',
        'location_id',
        string='Raíces del árbol (mesa mover unidades RMA)',
        domain="[('usage', 'in', ('internal', 'view', 'transit')), '|', ('company_id', '=', False), ('company_id', '=', id)]",
        help='En la mesa de movimiento de unidades RMA, el primer nivel puede ser una sola raíz o varias '
        '(botones por cada ubicación). Si hay varias, el usuario elige primero la raíz y luego baja por el árbol.',
    )
    rma_move_desk_storage_category_include_ids = fields.Many2many(
        'stock.storage.category',
        'res_company_rma_move_desk_stor_cat_inc_rel',
        'company_id',
        'category_id',
        string='Mesa RMA: incluir solo categorías de almacenamiento',
        help='Si está vacío, se consideran todas las categorías. Si elige categorías, solo se muestran y '
        'permiten ubicaciones con esa categoría de almacenamiento (las sin categoría quedan fuera).',
    )
    rma_move_desk_storage_category_exclude_ids = fields.Many2many(
        'stock.storage.category',
        'res_company_rma_move_desk_stor_cat_exc_rel',
        'company_id',
        'category_id',
        string='Mesa RMA: excluir categorías de almacenamiento',
        help='Si está vacío, no se excluye ninguna categoría por este criterio. Las categorías aquí '
        'indicadas no aparecen en el selector ni son válidas como destino.',
    )
