# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class RmaPricelistItemDatesWizard(models.TransientModel):
    _name = 'rma.pricelist.item.dates.wizard'
    _description = 'Set validity dates on pricelist rules'

    pricelist_id = fields.Many2one(
        'product.pricelist',
        string='Pricelist',
        required=True,
    )
    date_start = fields.Datetime(string='Start date')
    date_end = fields.Datetime(string='End date')
    apply_scope = fields.Selection(
        [
            ('all', 'All rules'),
            ('no_dates', 'Only rules with no start and end date yet'),
        ],
        string='Apply to',
        required=True,
        default='no_dates',
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('active_model') == 'product.pricelist' and self.env.context.get('active_id'):
            res['pricelist_id'] = self.env.context['active_id']
        return res

    def action_apply(self):
        self.ensure_one()
        if self.date_start and self.date_end and self.date_start > self.date_end:
            raise UserError(_('Start date must be earlier than end date.'))
        domain = [('pricelist_id', '=', self.pricelist_id.id)]
        if self.apply_scope == 'no_dates':
            domain += [('date_start', '=', False), ('date_end', '=', False)]
        items = self.env['product.pricelist.item'].search(domain)
        if not items:
            raise UserError(_('No matching price rules to update.'))
        items.write({
            'date_start': self.date_start,
            'date_end': self.date_end,
        })
        return {'type': 'ir.actions.act_window_close'}
