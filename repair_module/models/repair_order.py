from odoo import models, fields, api, _

class RepairOrder(models.Model):
    _inherit = 'repair.order'
  
    account_partner_id = fields.Many2one(string='Owner Account', comodel_name='account.partner')
    origin = fields.Char(string='Origin')
    quality_check_id = fields.Many2one('quality.check', string="Quality Check")
    
    maintenance_type = fields.Selection([
        ('repair', 'Repair'),
        ('review', 'Review'),
        ('warranty', 'Warranty'),
        ('renew', 'Renew'),
    ])
    lifecycle_state = fields.Selection([
        ('A', 'A-Awaiting Inspection'),
        ('B', 'B-New'),
        ('C', 'C-Semi-new'),
        ('D', 'D-Repair'),
        ('E', 'E-Scrap'),
        ('F', 'F-Repair in review') 
    ], string='Lifecycle State')

    @api.onchange('account_partner_id')
    def _set_partner_and_owner(self):
        for sale in self:
            if sale.account_partner_id and sale.account_partner_id.partner_id:
                sale.partner_id = sale.account_partner_id.partner_id
            else:
                sale.partner_id = False


    ## Allows to assign the account_partner_id to the new sale.order
    def action_create_sale_order(self):
        res = super().action_create_sale_order()
        sale_orders = self.mapped('sale_order_id')
        for repair in self:
            if repair.sale_order_id and repair.account_partner_id:
                repair.sale_order_id.account_partner_id = repair.account_partner_id
        return res

    def action_validate(self):
        res = super().action_validate()  # O .action_confirm() dependiendo de tu versión
        self.picking_id.quality_alert_ids.stage_id = self.env.ref('quality.quality_alert_stage_2')
        return res

    def create(self, vals):
        res = super().create(vals) 
        res.picking_id.quality_alert_ids.stage_id = self.env.ref('quality.quality_alert_stage_2')
        return res

    def action_repair_start(self):
        res = super().action_repair_start()
        self.picking_id.quality_alert_ids.stage_id = self.env.ref('repair_module.quality_alert_stage_repairing')
        return res

    def action_repair_end(self):
        res = super().action_repair_end()
        self.picking_id.quality_alert_ids.stage_id = self.env.ref('repair_module.quality_alert_stage_sent_to_postsale')
        return res

    def open_quality_check(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id('quality_control.quality_check_action_team')

        related_quality_check = self.quality_check_id  # Asegúrate de que este campo exista

        action.update({
            'domain': [('id', 'in', related_quality_check.ids)],
            'context': {
                'default_quality_alert_ids': [(4, self.id)],
            },
            'views': [(False, 'list'), (False, 'form')],
        })

        if len(related_quality_check) == 1:
            action['views'] = [(False, 'form')]
            action['res_id'] = related_quality_check.id

        return action