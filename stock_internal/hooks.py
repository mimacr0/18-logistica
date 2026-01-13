# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2025 DaFe Solutions
#
##############################################################################


def post_init_hook(env):
    """Configure default settings for internal transfers"""
    _configure_internal_transfers(env)


def _configure_internal_transfers(env):
    """
    Set the default configuration for internal transfer operations.
    
    This configures all internal transfer picking types to require:
    - Mandatory scan of source location
    - Mandatory scan of destination location
    
    This ensures the flow: Scan Origin → Scan Product → Scan Destination
    """
    
    # Find all internal transfer picking types
    internal_picking_types = env['stock.picking.type'].search([
        ('code', '=', 'internal'),
    ])
    
    for picking_type in internal_picking_types:
        # Only update picking types that are actual internal transfers
        # (not QC, STOR, PACK which are also 'internal' code but have different purposes)
        sequence_code = picking_type.sequence_code or ''
        
        # Configure INT (Internal Transfers) with mandatory source and destination scan
        if sequence_code == 'INT':
            picking_type.write({
                'restrict_scan_source_location': 'mandatory',
                'restrict_scan_dest_location': 'mandatory',
            })
