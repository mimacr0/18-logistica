
from datetime import datetime
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ReceivePackageWizard(models.TransientModel):
    _name = 'receive.package.wizard'
    _description = 'Receive Package Wizard'

    @api.model
    def default_get(self, fields):
        res = super(ReceivePackageWizard, self).default_get(fields)
        res['receiver_id'] = self.env.user.employee_id.id
        return res

    search_tracking_ref = fields.Char(string='Search Tracking Reference')
    carrier_tracking_ref = fields.Char(string='Carrier Tracking Reference')
    global_tracking_ref = fields.Char(string='International Tracking Reference')
    package_name = fields.Char(string='Package Name')
    package_id = fields.Many2one(string='Package', comodel_name='stock.quant.package')
    package_type_id = fields.Many2one(string='Package Type', comodel_name='stock.package.type')
    picking_type_id = fields.Many2one('stock.picking.type', string='Picking Type')
    location_id = fields.Many2one('stock.location', string='Source Location')
    location_dest_id = fields.Many2one('stock.location', string='Destination Location')
    receiver_id = fields.Many2one('hr.employee', string='Receiver')
    height = fields.Char(string='Height', help="Packaging Height")
    width = fields.Char(string='Width', help="Packaging Width")
    packaging_length = fields.Char(string='Length', help="Packaging Length")
    weight = fields.Char(string='Weight', help="Weight")
    media_ids = fields.Many2many(string='Images / videos', comodel_name='ir.attachment')

    @api.onchange('search_tracking_ref')
    def _onchange_search_tracking_ref(self):
        package_id = False
        if self.search_tracking_ref:
            package_id = self.env['stock.quant.package'].search([
                '|', '|', 
                ('carrier_tracking_ref', '=', self.search_tracking_ref), 
                ('global_tracking_ref', '=', self.search_tracking_ref),
                ('name', '=', self.search_tracking_ref),
                ('state', 'in', ['on_hold', 'planned', 'in_progress'])  # Solo pendientes
                ], limit=1)
        
            self.package_id = package_id.id
            self.package_type_id = self.package_id.package_type_id.id if self.package_id.package_type_id else False
            self.carrier_tracking_ref = self.package_id.carrier_tracking_ref if self.package_id.carrier_tracking_ref else ''
            self.global_tracking_ref = self.package_id.global_tracking_ref if self.package_id.global_tracking_ref else ''
            self.weight = self.package_id.shipping_weight if self.package_id.shipping_weight else ''
            self.location_id = self.package_id.location_id.id if self.package_id.location_id else False
            if self.package_type_id:
                self.height = self.package_type_id.height
                self.width = self.package_type_id.width
                self.packaging_length = self.package_type_id.packaging_length
        else:
            self.package_id = False
            self.package_type_id = False
            self.carrier_tracking_ref = ''
            self.global_tracking_ref = ''
            self.weight = ''
            self.height = ''
            self.width = ''
            self.packaging_length = ''

    def _get_stock_barcode_model_data(self):
        return {
            'form_view_id': self.env.ref('stock_reception.action_receive_package_server').id,
            'info': {
                'icon': 'product-hunt',
                'message': _('Receive Package'),
            }
        }

    def attach_images(self):
       if self.media_ids:
            self.package_id.message_post(
                attachment_ids=self.media_ids.ids
            )
            self.media_ids.write({
                'res_id': self.package_id.id,
                'res_model': self.package_id._name
            })


    def action_confirm(self):
        # 1. Busca la línea de movimiento del paquete escaneado
        move_line = self.env['stock.move.line'].search([
            ('result_package_id', '=', self.package_id.id)
        ], limit=1)
        
        # 2. Obtiene el picking asociado
        picking = move_line.move_id.picking_id
        
        # 3. Asigna el receptor como responsable del picking
        if self.receiver_id and self.receiver_id.user_id:
            picking.user_id = self.receiver_id.user_id
        
        # 4. Valida el picking (confirma la recepción)
        picking.button_validate()
        
        # 5. Cambia el estado del paquete a "done"
        self.package_id.state = 'done'
        
        # 6. Adjunta las imágenes capturadas
        self.attach_images()
        
        # 7. Vuelve a abrir el wizard para escanear otro paquete
        action = self.env.ref('stock_reception.action_receive_package_server').read()[0]
        return action