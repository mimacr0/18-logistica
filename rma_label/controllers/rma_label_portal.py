# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2026 DaFe Solutions
#
##############################################################################

from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.http import request

class RmaLabelPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'rma_package_count' in counters:
            partner = request.env.user.partner_id
            package_count = request.env['stock.quant.package'].sudo().search_count([
                # ('owner_id', '=', partner.commercial_partner_id.id),
                ('type', '=', 'return')
            ])
            values['rma_package_count'] = package_count
        return values

    def _prepare_portal_layout_values(self):
        values = super()._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        package_count = request.env['stock.quant.package'].sudo().search_count([
            # ('owner_id', '=', partner.commercial_partner_id.id),
            ('type', '=', 'return')
        ])
        values['rma_package_count'] = package_count
        return values

    @http.route(['/my/rma_labels', '/my/rma_labels/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_rma_labels(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        Package = request.env['stock.quant.package'].sudo()

        domain = [
            # ('owner_id', '=', partner.commercial_partner_id.id),
            ('type', '=', 'return')
        ]

        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Reference'), 'order': 'name'},
        }
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        # count for pager
        package_count = Package.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/rma_labels",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=package_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        packages = Package.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])

        values.update({
            'date': date_begin,
            'packages': packages,
            'page_name': 'rma_label',
            'pager': pager,
            'default_url': '/my/rma_labels',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })
        return request.render("rma_label.portal_my_rma_labels", values)

    @http.route(['/my/rma_labels/create'], type='http', auth="user", website=True)
    def portal_rma_label_create(self, **kw):
        partner = request.env.user.partner_id
        commercial_partner = partner.commercial_partner_id
        
        # Get data for the form
        package_types = request.env['stock.package.type'].sudo().search([])
        account = request.env['account.partner'].sudo().search([('partner_id', '=', commercial_partner.id)], limit=1)
        product_mappings = request.env['account.product.map'].sudo().search([('account_id', '=', account.id)])
        
        # Sender partners (using logic from reference)
        company = request.env.user.company_id
        sender_address = partner.child_ids.filtered(lambda p: p.type == 'sender')
        sender_address = request.env['res.partner'].sudo().browse(company.partner_id.ids + commercial_partner.ids + sender_address.ids)
        
        # Delivery addresses
        delivery_addresses = partner.child_ids.filtered(lambda p: p.type == 'delivery')
        
        # Countries for the address modal
        countries = request.env['res.country'].sudo().search([])

        values = {
            'partner': partner,
            'package_types': package_types,
            'product_mappings': product_mappings,
            'sender_address': sender_address,
            'delivery_addresses': delivery_addresses,
            'countries': countries,
            'page_name': 'rma_label_form',
        }
        return request.render("rma_label.portal_rma_label_form", values)

    @http.route(['/my/rma_labels/save'], type='http', auth="user", methods=['POST'], website=True)
    def portal_rma_label_save(self, **post):
        partner = request.env.user.partner_id
        commercial_partner = partner.commercial_partner_id
        
        package_vals = {
            'owner_id': commercial_partner.id,
            'type': 'return',
            'rma_state': 'draft',
            'package_type_id': int(post.get('package_type_id')) if post.get('package_type_id') else False,
            'sender_id': int(post.get('sender_id')) if post.get('sender_id') else False,
            'carrier_id': int(post.get('carrier_id')) if post.get('carrier_id') else False,
            'notes': post.get('notes'),
        }
        
        package = request.env['stock.quant.package'].sudo().create(package_vals)
        
        # Handle products
        product_map_ids = request.httprequest.form.getlist('product_map_id')
        quantities = request.httprequest.form.getlist('quantity')
        
        for p_id, qty in zip(product_map_ids, quantities):
            if p_id and qty:
                request.env['rma.package.line'].sudo().create({
                    'package_id': package.id,
                    'product_map_id': int(p_id),
                    'quantity': float(qty),
                })
        
        return request.redirect('/my/rma_labels')

    @http.route(['/my/rma_labels/add_sender'], type='json', auth="user", methods=['POST'], website=True)
    def portal_rma_label_add_sender(self, **kw):
        partner = request.env.user.partner_id
        commercial_partner = partner.commercial_partner_id
        
        vals = {
            'name': kw.get('name'),
            'street': kw.get('street'),
            'city': kw.get('city'),
            'zip': kw.get('zip'),
            'country_id': int(kw.get('country_id')) if kw.get('country_id') else False,
            'phone': kw.get('phone'),
            'type': 'sender',
            'parent_id': commercial_partner.id,
        }
        
        new_partner = request.env['res.partner'].sudo().create(vals)
        return {
            'id': new_partner.id,
            'name': new_partner.name,
        }
