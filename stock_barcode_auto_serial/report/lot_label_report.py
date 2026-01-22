# -*- coding: utf-8 -*-
from odoo import api, models


class LotLabelReport(models.AbstractModel):
    _name = 'report.stock_barcode_auto_serial.report_lot_label'
    _description = 'Lot Label Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['stock.lot'].browse(docids)
        # Get account_name from data parameter
        account_name = data.get('account_name', '') if data else ''
        return {
            'doc_ids': docids,
            'doc_model': 'stock.lot',
            'docs': docs,
            'account_name': account_name,
        }
