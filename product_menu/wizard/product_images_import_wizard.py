
from odoo import fields, models, api


class ProductImagesImportWizard(models.TransientModel):
    _name = 'product.images.import.wizard'
    _description = 'PRODUCT IMAGES IMPORT WIZARD'

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True
    )
    image_ids = fields.Many2many(
        comodel_name='ir.attachment',
        string='Images',
        ondelete='cascade'
    )

    @api.onchange('image_ids')
    def onchange_image_ids(self):

        if not self.image_ids:
            return

        for image in self.image_ids:
            image.name = image.name

    def import_action(self):

        for image in self.image_ids:
            self.env['odoo.product.image'].create({
                'product_id': self.product_id.id,
                'product_tmpl_id': self.product_id.product_tmpl_id.id,
                'image': image.datas,
                'name': image.name
            })

        rules = self.env['rules'].sudo().search([])
        product = self.product_id

        for rule in rules:
            rule.execute_rule(product._name, product.id)
