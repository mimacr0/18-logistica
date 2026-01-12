def post_init_hook(env):
    _stock_expedition_initial_data(env)


def _stock_expedition_initial_data(env):
    """ Set the default configuration for stock expedition """

    # 1. Set the default configuration for stock expedition
    # NOTE: This configuration is duplicated in stock_reception/hooks.py
    # to ensure settings are applied regardless of installation order
    env['res.config.settings'].create({
        'group_stock_production_lot': True,
        'group_stock_multi_locations': True,
        'group_stock_adv_location': True,  # Multi-Step Routes
        'group_lot_on_delivery_slip': True,
        'group_product_variant': True
    }).execute()

    # 2. Configure delivery_steps = 'pick_pack_ship' (3 steps) in all warehouses
    warehouses = env['stock.warehouse'].search([])
    if warehouses:
        warehouses.write({
            'delivery_steps': 'pick_pack_ship',
        })

    # 3. Activar filtro de direcciones de envío en tipos Pick, Pack, Out
    expedition_types = env['stock.picking.type'].search([
        ('barcode', 'in', ['NV1PICK', 'NV1PACK', 'NV1OUT'])
    ])
    if expedition_types:
        expedition_types.write({
            'use_delivery_address_domain': True,
        })
