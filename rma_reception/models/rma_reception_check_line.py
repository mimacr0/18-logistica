# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class RmaReceptionCheckLine(models.Model):
    _name = 'rma.reception.check.line'
    _description = 'RMA package reception unpack check line'
    _order = 'template_sequence, id'

    package_id = fields.Many2one(
        'stock.quant.package',
        string='Package',
        required=True,
        ondelete='cascade',
        index=True,
    )
    template_id = fields.Many2one(
        'rma.reception.check.template',
        string='Check',
        required=True,
        ondelete='restrict',
    )
    template_sequence = fields.Integer(
        related='template_id.sequence',
        store=True,
        readonly=True,
    )
    failed = fields.Boolean(
        string='Failed',
        default=False,
        help='Set when this reception check did not pass.',
    )

    @api.onchange('failed')
    def _onchange_failed_set_package_incident(self):
        """Al marcar Failed en la lista editable, el onchange del paquete no corre; hace falta en la línea."""
        if not self.package_id:
            return
        pack = self.package_id
        if any(line.failed for line in pack.unpack_check_line_ids):
            pack.package_has_incident = True
        if self.failed:
            return {
                'warning': {
                    'title': _('Package incident'),
                    'message': _('The package has an incident.'),
                },
            }

    _sql_constraints = [
        (
            'rma_package_unpack_check_line_template_unique',
            'unique(package_id, template_id)',
            'Each checklist item can only appear once per package.',
        ),
    ]
