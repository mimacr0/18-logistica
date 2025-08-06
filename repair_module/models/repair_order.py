from odoo import models, fields, api, _
from .choices import MAINTENANCE_TYPE, LIFECYCLE_STATE

class RepairOrder(models.Model):
    _inherit = 'repair.order'

    account_partner_id = fields.Many2one(string='Owner Account', comodel_name='account.partner')
    origin = fields.Char(string='Origin')
    repair_alert_id = fields.Many2one( comodel_name='quality.alert', string='Alerta de Calidad', help='Alerta de calidad que generó este movimiento.')
    description = fields.Text(string="Problem Description")
    diagnosis_ids = fields.Many2many(comodel_name='repair.diagnosis', string='Diagnosis', relation='repair_order_repair_diagnosis_rel', column1='repair_id', column2='diagnosis_id')
    result_ids = fields.Many2many(comodel_name='repair.result', string='Results', relation='repair_order_repair_result_rel', column1='repair_id', column2='result_id')
    technician_id = fields.Many2one(comodel_name="res.users", string="Technician")
    maintenance_type = fields.Selection(MAINTENANCE_TYPE, string='Maintenance Type')

    lifecycle_state = fields.Selection(LIFECYCLE_STATE, string='Lifecycle State')
    confirm_date = fields.Datetime(string='Confirm Date')
    assigned_date = fields.Datetime(string='Assigned Date')
    assigned_user_id = fields.Many2one('res.users', string='Assigned User')
    in_progress_date = fields.Datetime(string='In Progress Date')
    in_progress_user_id = fields.Many2one('res.users', string='In Progress User')
    done_date = fields.Datetime(string='Done Date')
    done_user_id = fields.Many2one('res.users', string='Done User')
    
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
        if self.repair_alert_id:
            self.repair_alert_id.stage_id = self.env.ref('quality.quality_alert_stage_2')
        return res

    def create(self, vals):
        res = super().create(vals) 
        if self.repair_alert_id:
            res.repair_alert_id.stage_id = self.env.ref('quality.quality_alert_stage_2')
        return res

    def action_repair_start(self):
        res = super().action_repair_start()
        if self.repair_alert_id:
            self.repair_alert_id.stage_id = self.env.ref('repair_module.quality_alert_stage_repairing')
        return res

    def action_repair_end(self):
        res = super().action_repair_end()
        if self.repair_alert_id:
            self.repair_alert_id.stage_id = self.env.ref('repair_module.quality_alert_stage_sent_to_postsale')
        
        if self.lot_id:
            self.lot_id.diagnosis_ids = [(6, 0, self.diagnosis_ids.ids)]
            self.lot_id.result_ids = [(6, 0, self.result_ids.ids)]
        
        return res

    # def open_quality_check(self):
    #     self.ensure_one()
    #     action = self.env['ir.actions.actions']._for_xml_id('quality_control.quality_check_action_team')

    #     related_quality_check = self.quality_check_id  # Asegúrate de que este campo exista

    #     action.update({
    #         'domain': [('id', 'in', related_quality_check.ids)],
    #         'context': {
    #             'default_quality_alert_ids': [(4, self.id)],
    #             'default_repair_alert_id': record.repair_alert_id.id,
    #         },
    #         'views': [(False, 'list'), (False, 'form')],
    #     })

    #     if len(related_quality_check) == 1:
    #         action['views'] = [(False, 'form')]
    #         action['res_id'] = related_quality_check.id

    #     return action

    def return_to_after_sales(self):
        StockPicking = self.env['stock.picking']
        
        for record in self:
            location_repair = self.env['stock.location'].search([('barcode', '=', 'NV1P2S7')], limit=1)
            location_after_sales = self.env['stock.location'].search([('barcode', '=', 'NV1P2S4R')], limit=1)
            picking_type = self.env.ref('stock.picking_type_internal')

            if not location_repair or not location_after_sales:
                raise UserError("Faltan ubicaciones configuradas para el retorno a postventa.")

            picking_vals = {
                'picking_type_id': picking_type.id,
                'location_id': location_repair.id,
                'location_dest_id': location_after_sales.id,
                'origin': record.name or 'Repair ' + str(record.id),
                'partner_id': record.account_partner_id.partner_id.id if record.account_partner_id else False,
                'move_ids_without_package': [(0, 0, {
                    'name': record.product_id.display_name or '',
                    'product_id': record.product_id.id,
                    'product_uom_qty': record.product_qty,
                    'lot_ids': [(6, 0, [record.lot_id.id])] if record.lot_id else [],
                    'repair_id': record.id,
                })]
            }
            print("El lote que estamos moviendo es: ", record.lot_id.name)
            picking = StockPicking.create(picking_vals)

            # Tras crear el stock.picking, actualizamos el estado de quality.alert
            record.repair_alert_id.stage_id = self.env.ref('repair_module.quality_alert_stage_sent_to_postsale')