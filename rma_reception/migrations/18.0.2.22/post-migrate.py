# -*- coding: utf-8 -*-


def migrate(cr, version):
    """Backfill package_location_id from package_state for existing reception packages."""
    from odoo import api, SUPERUSER_ID

    env = api.Environment(cr, SUPERUSER_ID, {})
    Package = env['stock.quant.package'].sudo()
    cust = env.ref('rma_inventory.stock_location_rma_customer_final', raise_if_not_found=False)
    recv = env.ref('rma_inventory.stock_location_rma_reception', raise_if_not_found=False)
    unpack = env.ref('rma_inventory.stock_location_rma_unpack_zone', raise_if_not_found=False)
    if not Package._fields.get('package_location_id'):
        return
    for pack in Package.search([('package_location_id', '=', False)]):
        lid = False
        if pack.package_state == 'received' and recv:
            lid = recv.id
        elif pack.package_state in ('opened', 'done') and unpack:
            lid = unpack.id
        elif pack.package_state == 'draft' and cust:
            lid = cust.id
        if lid:
            pack.write({'package_location_id': lid})
