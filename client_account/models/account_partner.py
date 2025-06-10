##############################################################################
#
# Copyright 2025 DaFe Solutions
#
##############################################################################

from odoo import models, fields, api, _

class AccountPartner(models.Model):
    _name = 'account.partner'
    _description = 'Account Partner'

    name = fields.Char(string='Name', copy=False)
    partner_id = fields.Many2one('res.partner', string='Partner')