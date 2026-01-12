# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2025 DaFe Solutions
#
##############################################################################


def post_init_hook(env):
    """Activa la opción de fechas de caducidad en productos."""
    env['res.config.settings'].create({
        'group_product_expiry': True,
    }).execute()
