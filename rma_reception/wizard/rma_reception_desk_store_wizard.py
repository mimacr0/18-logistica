# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class RmaReceptionDeskStoreWizard(models.TransientModel):
    _name = 'rma.reception.desk.store.wizard'
    _description = 'Unpack desk — store RMA units or quants with chosen locations'

    package_id = fields.Many2one('stock.quant.package', string='Package', readonly=True)
    line_ids = fields.One2many(
        'rma.reception.desk.store.wizard.line',
        'wizard_id',
        string='Lines',
        required=True,
    )

    def action_confirm(self):
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_('No lines to process.'))
        for line in self.line_ids:
            if not line.location_id:
                raise UserError(_('Each line must have a storage location.'))
            if line.line_type == 'rma_unit':
                line.rma_unit_id.with_context(rma_transition_reason=_('Store')).write({
                    'state': 'stored',
                    'location_id': line.location_id.id,
                })
            else:
                q = line.quant_id
                if not q or q.quantity <= 0:
                    raise UserError(_('Invalid or empty quant on line %s.') % line.display_name)
                q.sudo().move_quants(
                    location_dest_id=line.location_id,
                    unpack=True,
                    message=_('Unpack desk — store'),
                )
        return {'type': 'ir.actions.act_window_close'}


class RmaReceptionDeskStoreWizardLine(models.TransientModel):
    _name = 'rma.reception.desk.store.wizard.line'
    _description = 'Unpack desk store line'
    _order = 'id'

    wizard_id = fields.Many2one(
        'rma.reception.desk.store.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade',
    )
    line_type = fields.Selection(
        [
            ('rma_unit', 'RMA unit'),
            ('quant', 'Stock quant'),
        ],
        string='Type',
        required=True,
    )
    rma_unit_id = fields.Many2one('rma.unit', string='RMA unit', ondelete='cascade')
    quant_id = fields.Many2one('stock.quant', string='Quant', ondelete='cascade')
    location_id = fields.Many2one(
        'stock.location',
        string='Storage location',
        required=True,
        domain="[('usage', '=', 'internal')]",
    )
    display_name = fields.Char(string='Item', compute='_compute_display_name')

    @api.depends('line_type', 'rma_unit_id', 'rma_unit_id.name', 'rma_unit_id.account_sku',
                 'quant_id', 'quant_id.product_id', 'quant_id.quantity', 'quant_id.lot_id')
    def _compute_display_name(self):
        for line in self:
            if line.line_type == 'rma_unit' and line.rma_unit_id:
                u = line.rma_unit_id
                sku = u.account_sku or ''
                line.display_name = '%s%s' % (u.name, (' — %s' % sku) if sku else '')
            elif line.line_type == 'quant' and line.quant_id:
                q = line.quant_id
                prod = q.product_id.display_name if q.product_id else _('Product')
                parts = [prod, str(q.quantity)]
                if q.lot_id:
                    parts.append('(%s)' % q.lot_id.name)
                line.display_name = ' — '.join(parts)
            else:
                line.display_name = _('Line')

    @api.constrains('line_type', 'rma_unit_id', 'quant_id')
    def _check_line_ref(self):
        for line in self:
            if line.line_type == 'rma_unit':
                if not line.rma_unit_id or line.quant_id:
                    raise ValidationError(_('RMA unit lines must reference an RMA unit only.'))
            elif line.line_type == 'quant':
                if not line.quant_id or line.rma_unit_id:
                    raise ValidationError(_('Quant lines must reference a stock quant only.'))
