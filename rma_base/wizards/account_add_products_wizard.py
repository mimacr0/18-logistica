# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class RmaAddProductMapWizard(models.TransientModel):
    _name = 'rma.add.product.map.wizard'
    _description = 'Select client account and product for a new product map'

    account_id = fields.Many2one(
        'account.partner',
        string='Client account',
        required=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        domain="[('type', '!=', 'service')]",
    )
    selection_type = fields.Selection([
        ('normal', 'Normal'),
        ('spare_parts', 'Spare Parts'),
    ], string='Selection Type', default='normal')
    
    warning_message = fields.Text(
        string=' ',
        readonly=True,
    )

    @api.onchange('account_id', 'product_id')
    def _onchange_account_product_clear_warning(self):
        self.warning_message = False

    def action_open_product_map(self):
        """Open a new account.product.map with account and product prefilled."""
        self.ensure_one()
        Map = self.env['account.product.map']
        existing = Map.search(
            [
                ('account_id', '=', self.account_id.id),
                ('product_id', '=', self.product_id.id),
                ('active', '=', True),
            ],
            limit=1,
        )
        if existing:
            self.write({
                'warning_message': _(
                    'A product map already exists for this client account and internal product '
                    '(%(name)s). Change the account or product, or edit the existing map from '
                    'the Product Map list.'
                ) % {'name': existing.display_name},
            })
            return {
                'type': 'ir.actions.act_window',
                'name': _('New product map'),
                'res_model': self._name,
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
                'views': [(self.env.ref('rma_base.view_rma_add_product_map_wizard_form').id, 'form')],
            }
        self.write({'warning_message': False})
        return {
            'type': 'ir.actions.act_window',
            'name': _('Product map'),
            'res_model': 'account.product.map',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                **self.env.context,
                'default_account_id': self.account_id.id,
                'default_product_id': self.product_id.id,
            },
        }
