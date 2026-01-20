def post_init_hook(env):
    _stock_reception_initial_data(env)


def _stock_reception_initial_data(env):
    """ Set the default configuration for stock reception """

    # 1. Set the default configuration for stock reception
    # NOTE: This configuration is duplicated in stock_expedition/hooks.py
    # to ensure settings are applied regardless of installation order
    env['res.config.settings'].create({
        'group_stock_production_lot': True,
        'group_stock_multi_locations': True,
        'group_stock_adv_location': True,  # Multi-Step Routes
        # 'group_stock_storage_categories': True,
        'group_lot_on_delivery_slip': True,
        'group_product_variant': True
    }).execute()

    # 2. Configure reception_steps = 'three_steps' in all warehouses
    warehouses = env['stock.warehouse'].search([])
    if warehouses:
        warehouses.write({
            'reception_steps': 'three_steps',
        })

        # 3. Configure picking types for 3-step reception
        for wh in warehouses:
            # Recepciones (in_type_id): No crear ni usar lotes existentes
            if wh.in_type_id:
                wh.in_type_id.write({
                    'use_create_lots': False,
                    'use_existing_lots': False,
                })

            # Quality Control (qc_type_id): Crear lotes, no usar existentes
            if wh.qc_type_id:
                wh.qc_type_id.write({
                    'use_create_lots': True,
                    'use_existing_lots': False,
                    'require_scan_confirmation': True,
                    # Solo permitir destino QC
                    'allowed_location_dest_ids': [(6, 0, [wh.wh_qc_stock_loc_id.id])] if wh.wh_qc_stock_loc_id else False,
                })
            if wh.store_type_id:
                wh.store_type_id.write({
                    'require_scan_confirmation': True,
                })

    # 4. Add the reception admin group to the admin user
    env.ref("base.user_admin").write({
        'groups_id': [(4, env.ref("stock_reception.group_package_reception_manager").id)]
    })
