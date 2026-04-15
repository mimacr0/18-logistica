# -*- coding: utf-8 -*-
from odoo import _, http
from odoo.http import request
from odoo.exceptions import UserError, AccessError
from odoo.osv.expression import AND


_ALLOWED_PACKAGE_DESK_METHODS = frozenset({
    'action_unpack_desk_open_store_wizard_rma',
    'action_unpack_desk_open_store_wizard_quants',
    'action_unpack_desk_move_to_storage',
    'action_unpack_desk_move_to_review',
    'action_unpack_desk_move_to_repair',
    'action_unpack_desk_move_to_scrap',
    'action_unpack_rma',
    'action_unpack_quant',
})
_ALLOWED_RMA_UNIT_DESK_METHODS = frozenset({
    'action_rma_to_review',
    'action_rma_to_repair',
    'action_rma_to_scrap',
})

_PACKAGE_SEARCH_FIELDS = [
    'id', 'name', 'customer_reference', 'package_state', 'package_has_incident',
    'package_location_id',
    'carrier_id', 'sender_id', 'type',
]


class RmaReceptionDeskController(http.Controller):
    @http.route('/rma_reception/desk/reception_wizard_form_view_id', type='json', auth='user')
    def reception_wizard_form_view_id(self):
        ref = request.env['ir.model.data'].check_object_reference(
            'rma_reception', 'view_rma_reception_package_wizard_form_desk',
        )
        return ref[1] if ref else False

    def _domain_reception_desk(self):
        """Waiting packages only (draft) — door reception queue."""
        return [('package_state', '=', 'draft')]

    def _domain_unpack_pending(self):
        """Received, no open incident flag — normal unpack queue."""
        return ['&', ('package_state', '=', 'received'), ('package_has_incident', '=', False)]

    def _domain_unpack_incident_list(self):
        """Any package with incident flag (e.g. received+incident or opened+incident)."""
        return [('package_has_incident', '=', True)]

    @http.route('/rma_reception/desk/packages_search', type='json', auth='user')
    def packages_search(self, mode, term):
        term = (term or '').strip()
        Package = request.env['stock.quant.package']
        if mode == 'reception':
            base_domain = self._domain_reception_desk()
        elif mode == 'unpack':
            base_domain = self._domain_unpack_pending()
        else:
            raise UserError(_('Invalid desk mode.'))
        term_domain = [
            '|', '|',
            ('name', 'ilike', term),
            ('customer_reference', 'ilike', term),
            ('notes', 'ilike', term),
        ]
        domain = AND([base_domain, term_domain])
        return Package.search_read(domain, _PACKAGE_SEARCH_FIELDS, order='id desc', limit=15)

    @http.route('/rma_reception/desk/packages_door_list', type='json', auth='user')
    def packages_door_list(self, mode, list_kind=None):
        Package = request.env['stock.quant.package']
        if mode == 'reception':
            domain = self._domain_reception_desk()
        elif mode == 'unpack':
            if list_kind == 'incident':
                domain = self._domain_unpack_incident_list()
            else:
                domain = self._domain_unpack_pending()
        else:
            raise UserError(_('Invalid desk mode.'))
        return Package.search_read(domain, _PACKAGE_SEARCH_FIELDS, order='id desc', limit=80)

    @http.route('/rma_reception/desk/packages_unpack_desk_counts', type='json', auth='user')
    def packages_unpack_desk_counts(self):
        """Contadores mesa unpack: pendientes (recibido sin incidencia) e incidencias."""
        Package = request.env['stock.quant.package']
        return {
            'pending': Package.search_count(self._domain_unpack_pending()),
            'incident': Package.search_count(self._domain_unpack_incident_list()),
        }

    @http.route('/rma_reception/desk/unpack_package_detail', type='json', auth='user')
    def unpack_package_detail(self, package_id):
        """Datos del bulto y líneas declaradas para la vista embebida de la mesa Unpack."""
        Package = request.env['stock.quant.package']
        pkg = Package.browse(int(package_id))
        if not pkg.exists():
            return {}
        pkg._sync_reception_check_lines()
        field = Package._fields['type']
        sel = field.selection
        if callable(sel):
            sel = sel(Package)
        type_labels = dict(sel)
        Quants = request.env['stock.quant']
        line_vals = []
        for line in pkg.package_products_line_ids.sorted('id'):
            loc_label = ''
            if line.product_map_id and line.product_map_id.product_id:
                q = Quants.search([
                    ('package_id', '=', pkg.id),
                    ('product_id', '=', line.product_map_id.product_id.id),
                    ('quantity', '>', 0),
                ], limit=1)
                if q:
                    loc_label = q.location_id.display_name
            if not loc_label and pkg.location_id:
                loc_label = pkg.location_id.display_name
            line_vals.append({
                'id': line.id,
                'quantity': line.quantity,
                'received_qty': line.received_qty,
                'product_map_name': line.product_map_id.display_name if line.product_map_id else '',
                'pending_unpack': bool(line.unpacked),
                'location_label': loc_label or '',
            })
        check_vals = []
        for cl in pkg.unpack_check_line_ids.sorted('template_sequence', 'id'):
            check_vals.append({
                'id': cl.id,
                'name': cl.template_id.name if cl.template_id else '',
                'failed': bool(cl.failed),
            })
        return {
            'id': pkg.id,
            'name': pkg.name,
            'display_name': pkg.display_name,
            'type': pkg.type,
            'type_label': type_labels.get(pkg.type, pkg.type or ''),
            'shipping_weight': pkg.shipping_weight,
            'weight_uom_name': pkg.weight_uom_name or '',
            'location_label': pkg.location_id.display_name if pkg.location_id else '',
            'package_location_label': pkg.package_location_id.display_name if pkg.package_location_id else '',
            'lines': line_vals,
            'check_lines': check_vals,
            'can_unpack': any(l['pending_unpack'] for l in line_vals),
        }

    @http.route('/rma_reception/desk/post_unpack_package_label', type='json', auth='user')
    def post_unpack_package_label(self, package_id):
        pkg = request.env['stock.quant.package'].browse(int(package_id))
        if not pkg.exists():
            return {}
        data = pkg.read(['display_name', 'name'])
        return data[0] if data else {}

    @http.route('/rma_reception/desk/post_unpack_units', type='json', auth='user')
    def post_unpack_units(self, package_id):
        Unit = request.env['rma.unit']
        domain = [
            ('package_id', '=', int(package_id)),
            ('active', '=', True),
            ('state', '=', 'received'),
        ]
        return Unit.search_read(
            domain,
            ['id', 'name', 'display_name', 'account_sku', 'state'],
            order='id asc',
        )

    @http.route('/rma_reception/desk/post_unpack_quants', type='json', auth='user')
    def post_unpack_quants(self, package_id):
        Quant = request.env['stock.quant']
        domain = [
            ('package_id', '=', int(package_id)),
            ('quantity', '>', 0),
        ]
        return Quant.search_read(
            domain,
            ['id', 'product_id', 'quantity', 'location_id', 'lot_id'],
            order='id asc',
        )

    @http.route('/rma_reception/desk/rma_unit_call', type='json', auth='user')
    def rma_unit_call(self, method, unit_ids):
        if method not in _ALLOWED_RMA_UNIT_DESK_METHODS:
            raise AccessError('Method not allowed.')
        ids = [int(x) for x in (unit_ids or [])]
        if not ids:
            raise UserError('No RMA unit ids.')
        units = request.env['rma.unit'].browse(ids)
        fn = getattr(units, method)
        return fn()

    @http.route('/rma_reception/desk/package_call', type='json', auth='user')
    def package_call(
        self,
        method,
        package_id,
        desk_store_rma_unit_ids=None,
        desk_store_quant_ids=None,
        desk_unpack_incident_line_ids=None,
    ):
        if method not in _ALLOWED_PACKAGE_DESK_METHODS:
            raise AccessError('Method not allowed.')
        pkg = request.env['stock.quant.package'].browse(int(package_id))
        ctx = dict(request.env.context)
        if method in ('action_unpack_rma', 'action_unpack_quant'):
            ctx['package_unpack_desk'] = True
            if desk_unpack_incident_line_ids is not None:
                ctx['desk_unpack_incident_line_ids'] = [
                    int(x) for x in desk_unpack_incident_line_ids
                ]
        if desk_store_rma_unit_ids is not None:
            ctx['desk_store_rma_unit_ids'] = [int(x) for x in desk_store_rma_unit_ids]
        if desk_store_quant_ids is not None:
            ctx['desk_store_quant_ids'] = [int(x) for x in desk_store_quant_ids]
        fn = getattr(pkg.with_context(**ctx), method)
        return fn()
