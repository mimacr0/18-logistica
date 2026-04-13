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
    product_price = fields.Float(string='Internal Price', related='product_id.lst_price', readonly=True)

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


    is_spare_parts = fields.Boolean(related="product_id.product_tmpl_id.is_spare_parts", store=True)
    
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
    mapping_image_1920 = fields.Image("Mapping Image", max_width=1920, max_height=1920)

    # Resized fields stored (as attachment) for performance
    mapping_image_1024 = fields.Image("Mapping Image 1024", related="mapping_image_1920", max_width=1024, max_height=1024, store=True)
    mapping_image_512 = fields.Image("Mapping Image 512", related="mapping_image_1920", max_width=512, max_height=512, store=True)
    mapping_image_256 = fields.Image("Mapping Image 256", related="mapping_image_1920", max_width=256, max_height=256, store=True)
    mapping_image_128 = fields.Image("Mapping Image 128", related="mapping_image_1920", max_width=128, max_height=128, store=True)

    # Computed fields that are used to create a fallback to the template if
    # necessary, it's recommended to display those fields to the user.
    image_1920 = fields.Image("Image", compute='_compute_image_1920', inverse='_set_image_1920')
    image_1024 = fields.Image("Image 1024", compute='_compute_image_1024')
    image_512 = fields.Image("Image 512", compute='_compute_image_512')
    image_256 = fields.Image("Image 256", compute='_compute_image_256')
    image_128 = fields.Image("Image 128", compute='_compute_image_128')

    template_name = fields.Char(string='Custom Name')
    attributes = fields.Char(string='Attributes', compute='_compute_attributes', store=True)

    @api.depends('product_id.product_template_attribute_value_ids')
    def _compute_attributes(self):
        for record in self:
            if record.product_id:
                record.attributes = ", ".join(record.product_id.product_template_attribute_value_ids.mapped('name'))
            else:
                record.attributes = False

    @api.depends('mapping_image_1920', 'product_id.image_1920')
    def _compute_image_1920(self):
        for record in self:
            record.image_1920 = record.mapping_image_1920 or record.product_id.image_1920

    def _set_image_1920(self):
        for record in self:
            record.mapping_image_1920 = record.image_1920

    @api.depends('mapping_image_1024', 'product_id.image_1024')
    def _compute_image_1024(self):
        for record in self:
            record.image_1024 = record.mapping_image_1024 or record.product_id.image_1024

    @api.depends('mapping_image_512', 'product_id.image_512')
    def _compute_image_512(self):
        for record in self:
            record.image_512 = record.mapping_image_512 or record.product_id.image_512

    @api.depends('mapping_image_256', 'product_id.image_256')
    def _compute_image_256(self):
        for record in self:
            record.image_256 = record.mapping_image_256 or record.product_id.image_256

    @api.depends('mapping_image_128', 'product_id.image_128')
    def _compute_image_128(self):
        for record in self:
            record.image_128 = record.mapping_image_128 or record.product_id.image_128


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
