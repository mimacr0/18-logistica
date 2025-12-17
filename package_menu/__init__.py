# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2024 DaFe Solutions
#
##############################################################################

from . import models
# from . import wizard

def post_init_hook(env):
    from . import hooks
    hooks.post_init_hook(env)
