# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class BarcodeLocationsController(http.Controller):

    @http.route('/stock/barcode/locations/main', type='http', auth='user')
    def barcode_locations_main(self, **kwargs):
        session_info = request.env['ir.http'].session_info()
        return request.render('barcode_locations.barcode_locations_main', {
            'session_info': session_info,
            'json': json,
        })
