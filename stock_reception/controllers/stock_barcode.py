
import logging

from odoo import http, _
from odoo.http import request, route

from odoo.addons.stock_barcode.controllers.stock_barcode import StockBarcodeController

_logger = logging.getLogger(__name__)

class StockPackageController(http.Controller):

    @route('/stock/reception/get/model/data', type='json', auth="user")
    def stock_reception_package_model_data(self, model, res_id):
        if not res_id:
            target_record = request.env[model]
        else:
            target_record = request.env[model].browse(res_id)
        data = target_record._get_stock_barcode_model_data()
        return {
            'data': data
        }
