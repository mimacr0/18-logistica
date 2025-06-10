# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools.image import ImageProcess
import base64

'''
Esta clase en odoo 17 es originaria de connect Buyes, pero creo que sería interesante que 
perteneciese directamente a product_menu y que en connect_buyes haya una clase hija
Creo que tener imágenes fuera de la conexión con buyes puede ser útil para otras implementaciones
'''

class ProductImage(models.Model):
    _name = 'odoo.product.image'
    _description = 'Product Image'
    _order = "sequence, id"

    product_id = fields.Many2one('product.product', ondelete='cascade')
    product_tmpl_id = fields.Many2one('product.template', ondelete='cascade')
    image = fields.Binary(string='Image', required=True)
    name = fields.Char(string="Description")
    product_variant_name = fields.Char(compute='_compute_product_variant_name')
    sequence = fields.Integer(default=10)
    send_buyes = fields.Boolean(default=False)

    def _compute_product_variant_name(self):
        for rec in self:
            if rec.product_id and rec.product_id.product_variant_count > 1:
                variant = rec.product_id.product_template_attribute_value_ids._get_combination_name() or rec.product_id.display_name
                rec.product_variant_name = "Variant: " + variant
            else:
                rec.product_variant_name = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('product_tmpl_id'):
                vals['product_tmpl_id'] = self.env["product.product"].browse(vals['product_id']).product_tmpl_id.id

            if "image" in vals:
                vals["image"] = self.resize_image(vals['image'])

        return super(ProductImage, self).create(vals_list)

    def resize_image(self, image):
        parameter = self.env['ir.config_parameter'].sudo().get_param('product.image.resolution')
        if not parameter:
            return image

        width, height = [int(i) for i in parameter.upper().split('X')]
        if width <= 0 or height <= 0:
            return image

        img = ImageProcess(base64.b64decode(image))
        img = img.resize(width, height)
        image_data = img.image_quality()
        return base64.b64encode(image_data)

    def write(self, vals):
        if "image" in vals:
            vals["image"] = self.resize_image(vals['image'])
        res = super(ProductImage, self).write(vals)
        return res

