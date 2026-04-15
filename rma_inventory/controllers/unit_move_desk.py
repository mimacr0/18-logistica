# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.tools.float_utils import float_compare


class RmaInventoryUnitMoveDeskController(http.Controller):
    @http.route('/rma_inventory/desk/move/search_units', type='json', auth='user')
    def move_search_units(self, term):
        term = (term or '').strip()
        Unit = request.env['rma.unit']
        domain = [
            '&',
            ('active', '=', True),
            '|', '|', '|',
            ('name', 'ilike', term),
            ('account_sku', 'ilike', term),
            ('serial', 'ilike', term),
            ('imei', 'ilike', term),
        ]
        return Unit.search_read(
            domain,
            [
                'id',
                'name',
                'display_name',
                'account_sku',
                'serial',
                'imei',
                'state',
                'location_id',
                'account_product_map_id',
            ],
            limit=20,
            order='id desc',
        )

    @http.route('/rma_inventory/desk/move/search_quants', type='json', auth='user')
    def move_search_quants(self, term):
        term = (term or '').strip()
        if len(term) < 2:
            return []
        Quant = request.env['stock.quant']
        Quant.check_access_rights('read')
        # Mapa cliente: name, SKU, EAN, FNSKU, ASIN, template_name. Ubicación: solo barcode (no product_id).
        domain = [
            ('quantity', '>', 0),
            ('location_id.usage', '=', 'internal'),
            '|',
            '|',
            '|',
            '|',
            '|',
            '|',
            ('account_product_map_id.name', 'ilike', term),
            ('account_product_map_id.account_sku', 'ilike', term),
            ('account_product_map_id.account_ean13', 'ilike', term),
            ('account_product_map_id.account_fnsku', 'ilike', term),
            ('account_product_map_id.account_asin', 'ilike', term),
            ('account_product_map_id.template_name', 'ilike', term),
            ('location_id.barcode', 'ilike', term),
        ]
        quants = Quant.search(domain, limit=80, order='id desc')
        out = []
        for q in quants:
            rounding = q.product_uom_id.rounding
            if float_compare(q.available_quantity, 0, precision_rounding=rounding) <= 0:
                continue
            lot = q.lot_id
            loc = q.location_id
            mp = q.account_product_map_id
            out.append(
                {
                    'id': q.id,
                    'product_display_name': q.product_id.display_name,
                    'product_default_code': q.product_id.default_code or '',
                    'quantity': q.quantity,
                    'reserved_quantity': q.reserved_quantity,
                    'available_qty': q.available_quantity,
                    'location_id': [loc.id, loc.display_name] if loc else False,
                    'location_name': loc.complete_name if loc else '',
                    'location_barcode': loc.barcode or '',
                    'lot_name': lot.name if lot else '',
                    'map_name': mp.name if mp else '',
                    'map_account_sku': mp.account_sku or '' if mp else '',
                    'map_ean13': mp.account_ean13 or '' if mp else '',
                    'map_fnsku': mp.account_fnsku or '' if mp else '',
                    'map_asin': mp.account_asin or '' if mp else '',
                    'map_template_name': mp.template_name or '' if mp else '',
                }
            )
            if len(out) >= 20:
                break
        return out

    @http.route('/rma_inventory/desk/move/resolve_location_barcode', type='json', auth='user')
    def move_resolve_location_barcode(self, term):
        """Ubicación interna por código de barras (destino al escanear con líneas ya seleccionadas)."""
        term = (term or '').strip()
        if len(term) < 2:
            return {'status': 'short'}
        Location = request.env['stock.location']
        Location.check_access_rights('read')
        domain = [('usage', '=', 'internal'), ('barcode', '=', term)]
        locs = Location.search(domain, limit=5)
        if len(locs) > 1:
            return {'status': 'ambiguous', 'count': len(locs)}
        if len(locs) == 1:
            loc = locs[0]
            return {
                'status': 'ok',
                'location': {
                    'id': loc.id,
                    'name': loc.name,
                    'display_name': loc.display_name,
                    'usage': loc.usage,
                },
            }
        return {'status': 'not_found'}

    @http.route('/rma_inventory/desk/move/suggest_map_locations', type='json', auth='user')
    def move_suggest_map_locations(self, rma_unit_ids=None, quant_ids=None):
        return request.env['rma.unit'].move_desk_suggest_locations_by_maps(rma_unit_ids, quant_ids)

    @http.route('/rma_inventory/desk/move/root_locations', type='json', auth='user')
    def move_root_locations(self):
        return request.env['rma.unit'].move_desk_get_root_locations()

    @http.route('/rma_inventory/desk/move/location_children', type='json', auth='user')
    def move_location_children(self, parent_id):
        return request.env['rma.unit'].move_desk_location_children(int(parent_id))

    @http.route('/rma_inventory/desk/move/apply_destination', type='json', auth='user')
    def move_apply_destination(self, location_id, rma_unit_ids=None, quant_lines=None, unit_ids=None):
        """Aplica el movimiento y devuelve, por cada ítem, ``account.product.map`` y ``account.partner``."""
        rids = rma_unit_ids if rma_unit_ids is not None else unit_ids
        rids = [int(x) for x in (rids or [])]
        ql = quant_lines if quant_lines is not None else []
        return request.env['rma.unit'].move_desk_apply_mixed(
            int(location_id),
            rids,
            ql,
        )
