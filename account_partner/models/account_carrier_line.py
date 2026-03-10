##############################################################################
#
# Copyright 2026 DaFe Solutions
#
##############################################################################

from odoo import fields, models, api, _



class AccountCarrierLine(models.Model):
    _name = "account.carrier.line"
    _description = "Account Carrier Line"
    _order = 'sequence, id'

    sequence = fields.Integer(string='Sequence', default=10, help="Determine the display order")
    is_favorite = fields.Boolean(string='Favorite')
    partner_id = fields.Many2one('res.partner', string='Partner')

    def _clear_other_favorites(self, partner_id, exclude_id=None):
        domain = [('partner_id', '=', partner_id), ('is_favorite', '=', True)]
        if exclude_id:
            domain.append(('id', '!=', exclude_id))
        favorites = self.search(domain)
        if favorites:
            favorites.write({'is_favorite': False})

    def write(self, vals):
        if vals.get('is_favorite'):
            for record in self:
                record._clear_other_favorites(record.partner_id.id, record.id)
        return super(AccountCarrierLine, self).write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        records = super(AccountCarrierLine, self).create(vals_list)
        for record in records:
            if record.is_favorite:
                record._clear_other_favorites(record.partner_id.id, record.id)
        return records
