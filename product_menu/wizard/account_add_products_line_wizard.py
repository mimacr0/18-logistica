
from odoo import api, fields, models

class AddProductsLineWizard(models.TransientModel):
    _name = 'add.products.line.wizard'
    _description = 'Add Products Line Wizard'

    wizard_id = fields.Many2one(comodel_name='add.products.wizard', string='Wizard')
    attribute_id = fields.Many2one(comodel_name='product.attribute', string='Attribute')
    value_ids = fields.Many2many(comodel_name='product.attribute.value', string='Values')
