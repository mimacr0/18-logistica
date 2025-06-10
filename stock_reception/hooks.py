
def post_init_hook(env):
    _stock_reception_initial_data(env)


def _stock_reception_initial_data(env):
    """ Set the default configuration for stock reception """

    # Set the default configuration for stock reception
    env['res.config.settings'].create({
        'group_stock_production_lot': True,
        'group_stock_multi_locations': True,
        # 'group_stock_storage_categories': True,
        'group_lot_on_delivery_slip': True,
        'group_product_variant': True
    }).execute()

    # Add the reception admin group to the admin user
    env.ref("base.user_admin").write({
        'groups_id': [(4, env.ref("stock_reception.group_package_reception_manager").id)]
    })
