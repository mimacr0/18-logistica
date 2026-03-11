##############################################################################
#
# Copyright 2026 DaFe Solutions
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AccountProductMap(models.Model):
    _name = 'account.product.map'
    _description = 'Account Product Mapping'

    _rec_name = 'name'
    name = fields.Char(string='Name', compute='_compute_name', store=True)

    # Relaciones principales
    account_id = fields.Many2one('account.partner', string='Client Account', required=True, index=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Partner', related='account_id.partner_id', store=True, index=True)
    product_id = fields.Many2one('product.product', string='Internal Product', required=True, index=True)

    # Identificadores cliente

    account_sku = fields.Char(string='Account SKU', index=True)
    account_ean13 = fields.Char(string='EAN13', index=True)
    account_fnsku = fields.Char(string='FNSKU', index=True)
    account_asin = fields.Char(string='ASIN', index=True)

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

    @api.depends('account_id.name', 'product_id.name')
    def _compute_name(self):
        for record in self:
            account_name = record.account_id.name or ''
            product_name = record.product_id.name or ''
            if account_name and product_name:
                record.name = f"{account_name}-{product_name}"
            else:
                record.name = account_name or product_name or _('New Mapping')

    @api.constrains('account_ean13')
    def _check_ean13(self):
        for record in self:
            if record.account_ean13 and len(record.account_ean13) != 13:
                raise ValidationError(_("The EAN13 must have exactly 13 characters."))

    @api.model
    def _find_or_create_mapping(self, account_id, sku, product_id=None, **kwargs):
        """
        Busca un mapa por account y SKU. Si no lo encuentra, lo crea
        (siempre que exista un product_id asociado).
        """
        mapping = self.search([
            ('account_id', '=', account_id),
            ('account_sku', '=', sku)
        ], limit=1)
        
        if not mapping and product_id:
            vals = {
                'account_id': account_id,
                'product_id': product_id,
                'account_sku': sku,
            }
            vals.update(kwargs) # Añade campos adicionales como account_ean13, marketplace, etc.
            mapping = self.create(vals)
            
        return mapping
