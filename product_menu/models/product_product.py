
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

