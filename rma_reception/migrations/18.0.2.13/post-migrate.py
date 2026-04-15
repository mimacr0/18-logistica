# -*- coding: utf-8 -*-


def migrate(cr, version):
    from odoo import api, SUPERUSER_ID

    env = api.Environment(cr, SUPERUSER_ID, {})
    packages = env['stock.quant.package'].search([])
    if packages:
        packages._sync_unpack_check_lines()
