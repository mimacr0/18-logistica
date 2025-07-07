from odoo import models, fields, api, _

class RepairOrder(models.Model):
    _inherit = 'repair.order'
  
    account_partner_id = fields.Many2one(string='Owner Account', comodel_name='account.partner')
    origin = fields.Char(string='Origin')
    quality_check_id = fields.Many2one('quality.check', string="Quality Check")

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
        for repair in self:
            if repair.quality_check_id:
                repair.quality_check_id.repair_order_id = repair.id
        return res

    def create(self, vals):
        res = super().create(vals) 
        if res.quality_check_id:
            res.quality_check_id.repair_order_id = res.id
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