# -*- coding: utf-8 -*-
from odoo import models, fields, api


class RmaReceptionCheckTemplate(models.Model):
    _name = 'rma.reception.check.template'
    _description = 'RMA reception checklist item'
    _order = 'sequence, id'

    name = fields.Char(string='Check', required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    type = fields.Selection(
        [
            ('all', 'All package types'),
            ('return', 'Return package'),
            ('new', 'New package'),
        ],
        string='Package type',
        required=True,
        default='all',
        help='Only templates whose type matches the package (or “All”) are added to the checklist.',
    )

    @api.model
    def _get_templates_for_package(self, package):
        """Active templates compatible with this package type (`type` = all or same as package)."""
        if not package:
            return self.browse()
        pkg_type = package.type
        if not pkg_type:
            return self.browse()
        domain = [
            ('active', '=', True),
            '|',
            ('type', '=', 'all'),
            ('type', '=', pkg_type),
        ]
        return self.search(domain, order='sequence, id')
