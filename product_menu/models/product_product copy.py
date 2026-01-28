
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

    def check_product_default_code(self, code):
        for product in self:
            existing_product = self.env['product.product'].search([('default_code', '=', code)])
            if not existing_product:
                product.generate_product_code()
            else:
                return existing_product


    def generate_product_default_code(self, account_name, product_name, attributes):
        for product in self:
            name_part = (product.name or '')[:4].upper()
            partner_code = (product.account_partner_id.code or '').upper()

            # Obtener valores de atributos (solo para variantes)
            attributes = product.product_template_attribute_value_ids.mapped('name')
            attributes_part = '-'.join(attr.upper() for attr in attributes)

            product.default_code = f"{partner_code}-{name_part}-{attributes_part}"

    @api.model
    def find_by_barcode_or_sku(self, barcode=None, sku=None):
        """
        Busca un producto existente por código de barras o SKU.
        
        :param barcode: Código de barras del producto
        :param sku: SKU (default_code) del producto
        :return: product.product recordset (vacío si no se encuentra)
        """
        if not barcode and not sku:
            return self.env['product.product']
        
        domain = []
        if barcode:
            domain.append(('barcode', '=', barcode))
        if sku:
            domain.append(('default_code', '=', sku))
        
        # Si hay ambos, usar OR
        if len(domain) > 1:
            domain = ['|'] + domain
        
        return self.env['product.product'].search(domain, limit=1)

    def _clean_text_for_sku(self, text, max_length=None):
        """Limpia texto para usar en SKU: solo alfanuméricos, sin espacios, mayúsculas."""
        if not text:
            return ''
        cleaned = ''.join(c for c in text if c.isalnum() or c.isspace()).replace(' ', '').upper()
        return cleaned[:max_length] if max_length else cleaned

    def generate_default_code(self, account_partner=None):
        """
        Genera un default_code (SKU) para el producto basado en:
        - Nombre del account_partner
        - Primeras 4 letras del nombre del producto (mayúsculas)
        - Nombres de los valores de los atributos de esta variante (mayúsculas, en inglés)
        
        :param account_partner: account.partner record (opcional, si no se proporciona usa self.account_partner_id)
        :return: string con el SKU generado
        """
        self.ensure_one()
        
        sku_parts = []
        
        # Parte 1: Nombre del account_partner (máximo 10 caracteres)
        partner = account_partner or self.account_partner_id
        if partner and partner.name:
            partner_code = self._clean_text_for_sku(partner.name, 10)
            if partner_code:
                sku_parts.append(partner_code)
        
        # Parte 2: Primeras 4 letras del nombre del producto
        template = self.product_tmpl_id
        if template and template.name:
            product_code = self._clean_text_for_sku(template.name, 4)
            if product_code:
                sku_parts.append(product_code)
        
        # Parte 3: Valores de atributos de la variante (en inglés)
        attr_values_en = self.product_template_attribute_value_ids.with_context(lang='en_US')
        for attr_value in attr_values_en:
            if attr_value.name:
                value_code = self._clean_text_for_sku(attr_value.name)
                if value_code:
                    sku_parts.append(value_code)
        
        # Fallback: usar ID del producto si no hay partes
        if not sku_parts:
            sku_parts.append(f"PROD{self.id}" if self.id else "SKUTEMP")
        
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

    @api.model
    def find_and_ensure_sku(self, barcode=None, sku=None, account_partner=None):
        """
        Busca un producto por barcode o SKU, y si existe y no tiene SKU, le asigna uno.
        
        :param barcode: Código de barras del producto
        :param sku: SKU (default_code) del producto
        :param account_partner: account.partner record para generar SKU si es necesario
        :return: tuple (product.product recordset, bool indicando si se encontró)
        """
        existing_product = self.find_by_barcode_or_sku(barcode=barcode, sku=sku)
        if existing_product:
            existing_product.ensure_default_code(account_partner=account_partner)
            return existing_product, True
        return self.env['product.product'], False