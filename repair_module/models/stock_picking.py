from odoo import models, fields, api, _

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    alert_ids = fields.Many2many('quality.alert', 'quality_alert_picking_rel', string='Alerts', check_company=True)


