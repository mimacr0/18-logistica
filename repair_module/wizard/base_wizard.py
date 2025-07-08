# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2024 DaFe Solutions
#
##############################################################################

from odoo import api, fields, models, tools, _


class BaseWizard(models.TransientModel):
    _name = "base.wizard"
    _description = 'Base Wizard'