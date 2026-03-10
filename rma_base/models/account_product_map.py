##############################################################################
#
# Copyright 2026 DaFe Solutions
#
##############################################################################

from odoo import models, fields, api, _

class AccountProductMap(models.Model):
    _name = 'account.product.map'
    _description = 'Account Product Mapping'

    _rec_name = 'account_sku'

    # Relaciones principales
    account_id = fields.Many2one('account.partner', string='Client Account', required=True, index=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Partner', related='account_id.partner_id', store=True, index=True)
    product_id = fields.Many2one('product.product', string='Internal Product', required=True, index=True)

    # Identificadores cliente

    account_sku = fields.Char(string='Account SKU', index=True)
    account_ean13 = fields.Char(string='EAN13', index=True)
    account_fnsku = fields.Char(string='FNSKU', index=True)
    account_asin = fields.Char(string='ASIN', index=True)
    account_name = fields.Char(string='Account Product Name')

    # Marketplace
    marketplace = fields.Selection([
        ('amazon', 'Amazon'),
        ('cdiscount', 'Cdiscount'),
        ('ebay', 'eBay'),
        ('temu', 'Temu'),
        ('aliexpress', 'AliExpress'),
        ('pccomponentes', 'PcComponentes'),
        ('carrefour', 'Carrefour'),
        ('worten', 'Worten'),
        ('web', 'Webstore'),
        ('other', 'Other')
    ], index=True)

    # Tracking logic
    tracking = fields.Selection([
        ('none', 'No Tracking'),
        ('lot', 'Batch'),
        ('serial', 'Serial / IMEI')
    ], default='none')

    # Estado
    active = fields.Boolean(default=True)
    notes = fields.Text()

    _sql_constraints = [
        (
            'account_sku_unique',
            'unique(account_id, account_sku)',
            'account SKU must be unique per account'
        )
    ]
