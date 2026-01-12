# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2024 DaFe Solutions
#
##############################################################################


def post_init_hook(env):
    """Configura las ubicaciones permitidas para el tipo Move to Repair."""
    picking_type = env.ref('repair_module.stock_picking_type_move_to_repair', raise_if_not_found=False)
    repair_location = env.ref('repair_module.stock_location_repairs', raise_if_not_found=False)

    if picking_type and repair_location:
        picking_type.write({
            'allowed_location_dest_ids': [(6, 0, [repair_location.id])],
        })
