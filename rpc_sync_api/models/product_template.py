from odoo import models, fields, _
import json

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def update_product_ecommerce_translation(self, lang, text):
        self.ensure_one()
        query = """
            UPDATE product_template SET description_ecommerce = jsonb_set(description_ecommerce, '{{{}}}', %s::jsonb)
            WHERE id = %s
        """.format(lang)
        self.env.cr.execute(query, (json.dumps(text), self.id))
        self.env.cr.commit()
        return True
