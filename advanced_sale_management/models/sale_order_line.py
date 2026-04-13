##############################################################################
#
# Copyright 2026 DaFe Solutions
#
##############################################################################

from odoo import models, fields, api, _
from odoo.tools import html2plaintext
from odoo.exceptions import UserError
import json
from markupsafe import Markup
import logging

_logger = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    _description = 'Sale order line generalized'
    _order = 'name desc'


    package_id = fields.Many2one('stock.quant.package', string='Package/Bundle')