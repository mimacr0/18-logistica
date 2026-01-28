
from odoo import fields, models, api, _


class ProductProductInherit(models.Model):
    _inherit = 'product.product'

    account_partner_id = fields.Many2one(comodel_name='account.partner', string='Account Partner', compute='_compute_account_partner_id', store=True)
    image_ids = fields.One2many('odoo.product.image', 'product_id', string='Images')

    repair_price = fields.Monetary(string='Repair Price', readonly=False)
    warranty_price = fields.Monetary(string='Warranty Price', readonly=False)
    review_price = fields.Monetary(string='Review Price', readonly=False)
    renew_price = fields.Monetary(string='Renew Price', readonly=False)
    
    @api.depends('product_tmpl_id.account_partner_id')
    def _compute_account_partner_id(self):
        for product in self:
            product.account_partner_id = product.product_tmpl_id.account_partner_id.id

    def open_image_bulk_import(self):
        action = self.env["ir.actions.actions"]._for_xml_id("product_menu.product_images_import_wizard_action")
        action['context'] = {
            'default_product_id': self.id
        }
        return action

    def open_add_product_wizard(self):
        action = self.env["ir.actions.actions"]._for_xml_id("product_menu.action_product_menu_create_stock_picking")
        return action

    def _clean_text_for_sku(self, text, max_length=None):
        """Limpia texto para usar en SKU: solo alfanuméricos, sin espacios, mayúsculas."""
        if not text:
            return ''
        cleaned = ''.join(c for c in text if c.isalnum() or c.isspace()).replace(' ', '').upper()
        return cleaned[:max_length] if max_length else cleaned

    def generate_default_code(self, account_partner=None):
        """
        Genera un default_code (SKU) para el producto basado en:
        - ID de la cuenta del cliente (account_partner)
        - ID del product.template
        - ID del product.product
        
        Formato: {account_partner_id}-{template_id}-{product_id}
        
        :param account_partner: account.partner record (opcional, si no se proporciona usa self.account_partner_id)
        :return: string con el SKU generado
        """
        self.ensure_one()
        
        # Obtener account_partner
        partner = account_partner or self.account_partner_id
        
        # Obtener IDs
        partner_id = partner.id if partner else None
        template_id = self.product_tmpl_id.id if self.product_tmpl_id else None
        product_id = self.id if self.id else None
        
        # Construir SKU: partner_id-template_id-product_id
        sku_parts = []
        if partner_id:
            sku_parts.append(str(partner_id))
        if template_id:
            sku_parts.append(str(template_id))
        if product_id:
            sku_parts.append(str(product_id))
        
        # Si no hay IDs, usar fallback
        if not sku_parts:
            return "SKUTEMP"
        
        return '-'.join(sku_parts)

    def ensure_default_code(self, account_partner=None):
        """
        Asegura que el producto tenga un default_code.
        Si no lo tiene, lo genera y lo asigna.
        
        :param account_partner: account.partner record (opcional)
        :return: El default_code asignado (nuevo o existente)
        """
        self.ensure_one()
        
        if self.default_code:
            return self.default_code
        
        new_sku = self.generate_default_code(account_partner=account_partner)
        if new_sku:
            self.write({'default_code': new_sku})
            self.invalidate_recordset(['default_code'])
            return new_sku
        
        return False