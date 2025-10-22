# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2024 DaFe Solutions
#
##############################################################################

import odoo

# ----------------------------------------------------------
# Monkey patch release to set the edition as 'theme'
# ----------------------------------------------------------
odoo.release.version_info = odoo.release.version_info[:5] + ('t',)
if '+e' not in odoo.release.version:     # not already patched by packaging
    odoo.release.version = '{0}+t{1}{2}'.format(*odoo.release.version.partition('-'))

odoo.service.common.RPC_VERSION_1.update(
    server_version=odoo.release.version,
    server_version_info=odoo.release.version_info)
