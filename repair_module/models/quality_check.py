##############################################################################
#
# Copyright 2025 DaFe Solutions
#
##############################################################################

from odoo import models, fields, api, _


class QualityCheck(models.Model):
    _inherit = 'quality.check'

    is_repair_request = fields.Boolean(string="Repair/Review Request")
    repair_order_id = fields.Many2one('repair.order', string="Associated Technical Order")


    # Esto tiene que permitirme poner en el quality.check, el quality.alert
    # Cuado se crean, no se pasan por defecto, he probado a heredar el create, pero  en ese momento el stock.picking tampoco está relacionado con el quality.alert.
    # Tal vez, relacionándolo con button_validate o con action_confirm, habría qie comprobar más explícitamente el flujo que queremos seguir.
    # @api.depends('picking_id.quality_alert_ids')
    # def set_quality_alert(self, vals):
    #     for check in self:
    #         print("HOLA",check.picking_id)
    #         print(check.picking_id.quality_alert_ids)
    #         if check.picking_id and check.picking_id.quality_alert_ids:
    #             check.alert_ids = [(6, 0, check.picking_id.quality_alert_ids.ids)]
    #     return res

    def action_create_repair_order(self):
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Crear Orden de Reparación'),
            'res_model': 'repair.order',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_account_partner_id': self.picking_id.account_partner_id.id,
                'default_product_id': self.product_id.id,
                'default_product_qty': self.qty_line,
                'default_lot_id': self.lot_id.id,
                'default_origin': self.name,
                'default_partner_id': self.partner_id.id,
                'default_quality_check_id': self.id,
                
            },
            'views': [(self.env.ref('repair.view_repair_order_form').id, 'form')],
        }

    def open_repair_order(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id('repair.action_picking_repair')

        related_repair = self.repair_order_id  # Asegúrate de que este campo exista

        action.update({
            'domain': [('id', 'in', related_repair.ids)],
            'context': {
                'default_quality_alert_ids': [(4, self.id)],
            },
            'views': [(False, 'list'), (False, 'form')],
        })

        if len(related_repair) == 1:
            action['views'] = [(False, 'form')]
            action['res_id'] = related_repair.id

        return action
