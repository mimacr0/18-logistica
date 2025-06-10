##############################################################################
#
# Copyright 2025 DaFe Solutions
#
##############################################################################

from odoo import models, fields, api


class BaseModel(models.Model):
    _name = 'base.model'
    _description = 'Base Model'