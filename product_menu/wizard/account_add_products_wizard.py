from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AddProductsWizard(models.TransientModel):
    _name = 'add.products.wizard'
    _description = 'Add Products Wizard'

    account_partner_id = fields.Many2one(comodel_name='account.partner', string='Account')
    product_template_id = fields.Many2one(comodel_name='product.template', string='Product Template')
    name = fields.Char(string='Product',  copy=False, translate=True)
    image_1920 = fields.Binary(string='Image')
    tracking = fields.Selection(selection=[
        ('serial', 'By Unique Serial Number'),
        ('none', 'No Tracking')
    ], string='Tracking', default='none')
    weight = fields.Float(string='Weight', digits='Stock Weight')
    volume = fields.Float(string='Volume', digits='Stock Volume')
    product_tag_ids = fields.Many2many(comodel_name='product.tag', string='Tags')
    categ_id = fields.Many2one(comodel_name='product.category', string='Category')
    list_price = fields.Monetary(string='Sale Price')
    attr_line_ids = fields.One2many(comodel_name='add.products.line.wizard', inverse_name='wizard_id', string='Attributes')
    variant_ids = fields.Many2many(comodel_name='product.product', string='Variants')
    variant_count = fields.Integer(string='# Variants', compute='_compute_variant_count')
    currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    repair_price = fields.Monetary(string='Repair Price')
    warranty_price = fields.Monetary(string='Warranty Price')
    review_price = fields.Monetary(string='Review Price')
    renew_price = fields.Monetary(string='Renew Price')
    currency_id = fields.Many2one('res.currency', string='Currency', default=1)
    length = fields.Float(string="Length")
    width = fields.Float(string="Width")
    height = fields.Float(string="Height")

    @api.depends('variant_ids')
    def _compute_variant_count(self):
        for record in self:
            record.variant_count = len(record.variant_ids)

    @api.onchange('length', 'width', 'height')
    def _onchange_length_width_height(self):
        for record in self:
            if record.length and record.width and record.height:
                record.volume = record.length * record.width * record.height
            else:
                record.volume = 0

    def _check_product_info(self):
        error_message = ''
        if not self.account_partner_id:
            error_message += _('Please select the related account for the product\n')
        if not self.name:
            error_message += _('Please enter the name for the product\n')
        if not self.volume:
            error_message += _('Please enter the volume for the product\n')
        if not self.weight:
            error_message += _('Please enter the weight for the product\n')
        if not self.attr_line_ids:
            error_message += _('Please add attributes\n')
        if error_message:
            raise ValidationError(error_message)
        return True
    
    def action_add_product(self):
        self._check_product_info()
        ProductTemplate = self.env['product.template']
        values = {
            'name': self.name,
            'image_1920': self.image_1920,
            'weight': self.weight,
            'volume': self.volume,
            'product_tag_ids': self.product_tag_ids,
            'categ_id': self.categ_id.id,
            'tracking': self.tracking,
            'repair_price': self.repair_price,
            'warranty_price': self.warranty_price,
            'review_price': self.review_price,
            'renew_price': self.renew_price,
            'account_partner_id': self.account_partner_id.id,
            'is_storable': True,
        }
        if self.product_template_id:
            template = self.product_template_id
            attr_lines = []
            for line in self.attr_line_ids:
                tmpl_line = template.attribute_line_ids.filtered(lambda l: l.attribute_id == line.attribute_id)
                if tmpl_line:
                    tmpl_line.value_ids = [(6, 0, line.value_ids.ids)]
                else:
                    attr_lines.append((0, 0, {
                        'attribute_id': line.attribute_id.id,
                        'value_ids': [(6, 0, line.value_ids.ids)]
                    }))
            values.update({
                'attribute_line_ids': attr_lines
            })
            template.write(values)
        else:
            values.update({
                'attribute_line_ids': [(0, 0, {
                    'attribute_id': line.attribute_id.id,
                    'value_ids': [(6, 0, line.value_ids.ids)]
                }) for line in self.attr_line_ids]
            })
            template = ProductTemplate.create(values)
        self._cr.execute(f'select name from add_products_wizard where id = {self.id}')
        translate_values = self._cr.fetchall()
        template.update_field_translations('name', translate_values[0][0])
        template.product_variant_ids.write({
            'account_partner_id': self.account_partner_id.id,
            'image_1920': self.image_1920,
            'weight': self.weight,
            'volume': self.volume,
            'product_tag_ids': self.product_tag_ids,
            'repair_price': self.repair_price,
            'warranty_price': self.warranty_price,
            'review_price': self.review_price,
            'renew_price': self.renew_price,
            'is_storable': True,
        })
        template.write({
            'sale_ok': False,
            'purchase_ok': False,
            'type': 'consu',
            'list_price': 0,
            'taxes_id': False,
            'standard_price': 0,
            'tracking': self.tracking or 'none',
        })
        self.product_template_id = template.id

        return {
            'name': _('Products'),
            'type': 'ir.actions.act_window',
            'res_model': 'product.product',
            'view_type': 'kanban,tree,form',
            'domain': [('account_partner_id', '!=', False)],
            'search_view_id': self.env.ref('product_menu.product_menu_product_view_search').id,
            'views': [
                (self.env.ref('product.product_kanban_view').id, 'kanban'),
                (self.env.ref('product.product_variant_easy_edit_view').id, 'form')
            ],
            'context': self.env.context
        }
