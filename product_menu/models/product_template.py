
from odoo import fields, models, api


class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'

    repair_price = fields.Monetary(string='Repair Price')
    warranty_price = fields.Monetary(string='Warranty Price')
    review_price = fields.Monetary(string='Review Price')
    renew_price = fields.Monetary(string='Renew Price')
    account_partner_id = fields.Many2one(comodel_name='account.partner', string='Account Partner')
