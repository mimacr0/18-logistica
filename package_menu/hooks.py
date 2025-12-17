# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2025 DaFe Solutions
#
##############################################################################

def post_init_hook(env):
    """Activar el checkbox de gestión de paquetes en la configuración"""
    _activate_package_tracking(env)


def _activate_package_tracking(env):
    """Activa el checkbox 'Packages' en la configuración de inventario"""
    # Crear y ejecutar la configuración para activar el checkbox
    # Esto automáticamente aplicará el grupo stock.group_tracking_lot 
    # a todos los usuarios internos mediante grupos implícitos
    env['res.config.settings'].create({
        'group_stock_tracking_lot': True,
    }).execute()

