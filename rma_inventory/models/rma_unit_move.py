# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2026 DaFe Solutions
#
##############################################################################

from odoo import models, fields, _


class RmaUnitMove(models.Model):
    _name = 'rma.unit.move'
    _description = 'RMA Unit Move'
    _order = 'date desc, id desc'

    rma_unit_id = fields.Many2one('rma.unit', string='RMA Unit', required=True, ondelete='cascade', index=True)
    from_location_id = fields.Many2one('stock.location', string='From Location')
    to_location_id = fields.Many2one('stock.location', string='To Location')
    from_state = fields.Selection(
        [
            ('received', _('Received')),
            ('review', _('In review')),
            ('repair', _('In repair')),
            ('stored', _('Stored')),
            ('shipped', _('Shipped')),
        ],
        string='From state',
    )
    to_state = fields.Selection(
        [
            ('received', _('Received')),
            ('review', _('In review')),
            ('repair', _('In repair')),
            ('stored', _('Stored')),
            ('shipped', _('Shipped')),
        ],
        string='To state',
    )
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    date = fields.Datetime(string='Date', default=fields.Datetime.now, required=True)
    reason = fields.Char(string='Reason')
