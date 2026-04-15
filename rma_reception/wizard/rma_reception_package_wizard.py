# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class RmaReceptionPackageWizard(models.TransientModel):
    _name = 'rma.reception.package.wizard'
    _description = 'RMA door reception package wizard'

    package_id = fields.Many2one(
        'stock.quant.package',
        string='Linked package',
        help='If set, confirming updates this package instead of creating a new one.',
    )
    package_state = fields.Selection(
        related='package_id.package_state',
        string='Package state',
        readonly=True,
    )
    account_id = fields.Many2one(
        'account.partner',
        string='Account',
    )
    sender_id = fields.Many2one('res.partner', string='Sender')
    package_type = fields.Selection(
        [
            ('return', 'Return Package'),
            ('new', 'New Package'),
        ],
        string='Package type',
        required=True,
        default='return',
    )
    carrier_id = fields.Many2one(
        'delivery.carrier',
        string='Carrier',
    )
    expedition1 = fields.Char(
        string='Package reference / tracking',
        required=True,
        help='Main code or SSCC; becomes the package reference (name).',
    )
    expedition = fields.Char(string='Secondary reference')
    weight = fields.Float(string='Shipping weight', required=True)
    length = fields.Float(string='Length')
    width = fields.Float(string='Width')
    height = fields.Float(string='Height')
    with_incidence = fields.Boolean(string='Incident', default=False)
    media_ids = fields.Many2many(
        comodel_name='ir.attachment',
        relation='rma_reception_pkg_wizard_media_rel',
        column1='wizard_id',
        column2='attachment_id',
        string='Images / videos',
    )
    receiver_user_id = fields.Many2one(
        'res.users',
        string='Person receiving',
        default=lambda self: self.env.user,
        readonly=True,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        pkg_id = self.env.context.get('default_package_id')
        if not pkg_id:
            return res
        pack = self.env['stock.quant.package'].browse(pkg_id)
        if not pack.exists():
            return res
        res['package_id'] = pack.id
        vals_map = {
            'expedition1': pack.name or '',
            'expedition': pack.customer_reference or '',
            'weight': pack.shipping_weight if pack.shipping_weight and pack.shipping_weight > 0 else 1.0,
            'length': pack.packaging_length or 0.0,
            'width': pack.width or 0.0,
            'height': pack.height or 0.0,
            'carrier_id': pack.carrier_id.id,
            'package_type': pack.type or 'return',
            'sender_id': pack.sender_id.id if pack.sender_id else False,
            'with_incidence': pack.package_has_incident,
        }
        acc_id = pack._reception_default_account_partner_id()
        if acc_id:
            vals_map['account_id'] = acc_id
        if fields_list:
            for fname, val in vals_map.items():
                if fname in fields_list:
                    res[fname] = val
        else:
            res.update(vals_map)
        return res

    @api.constrains('weight')
    def _check_weight(self):
        for wiz in self:
            if wiz.weight <= 0:
                raise ValidationError(_('Weight must be greater than zero.'))

    @api.constrains('account_id', 'package_id')
    def _check_account_required_for_new(self):
        for wiz in self:
            if wiz.package_id:
                continue
            if not wiz.account_id:
                raise ValidationError(_('Account is required when creating a new package.'))

    def action_confirm(self):
        """Registra la recepción: Recibido; si hay incidencia, marca package_has_incident sin cambiar el flujo de estado. No desempaqueta."""
        self.ensure_one()
        if not self.account_id:
            raise ValidationError(_('Account is required.'))
        if self.package_id:
            self.package_id._reception_validate_confirm_prerequisites(
                self.account_id.id,
                carrier_id=self.carrier_id.id if self.carrier_id else 0,
                sender_id=self.sender_id.id if self.sender_id else 0,
                shipping_weight=self.weight,
                package_ref=self.expedition1,
            )
        else:
            if not self.carrier_id:
                raise ValidationError(_('Carrier is required.'))
            if not self.sender_id:
                raise ValidationError(_('Sender is required.'))
        had_package = bool(self.package_id)
        package = self._persist_reception_package()
        if not had_package:
            self.write({'package_id': package.id})
        desk = bool(self.env.context.get('package_reception_desk'))
        return {
            'type': 'ir.actions.client',
            'tag': 'rma_reception.clear_desk_search',
            'params': {'desk': desk},
        }

    def action_unpack(self):
        """Abre el checklist de desempaquetado (RMA o quants) según el tipo de bulto. Solo con estado Recibido."""
        self.ensure_one()
        if not self.carrier_id:
            raise ValidationError(_('Carrier is required.'))
        if not self.sender_id:
            raise ValidationError(_('Sender is required.'))
        if not self.package_id:
            raise UserError(_('Confirm reception first.'))
        if self.package_id.package_state != 'received':
            raise UserError(_('Unpack is only available when the package is in Received state.'))
        package = self._persist_reception_package()
        if self.env.context.get('package_reception_desk'):
            package = package.with_context(package_reception_desk=True)
        elif self.env.context.get('package_unpack_desk'):
            package = package.with_context(package_unpack_desk=True)
        if package.type == 'return':
            action = package.action_unpack_rma()
        else:
            action = package.action_unpack_quant()
        if action is False:
            raise UserError(_('Cannot start unpack: package type does not match the selected flow.'))
        return action

    def _attach_wizard_media_to_package(self, package):
        for att in self.media_ids:
            att.sudo().write({
                'res_model': 'stock.quant.package',
                'res_id': package.id,
            })
            package.message_post(attachment_ids=[att.id], message_type='comment')

    def _post_reception_chatter(self, package, created=False):
        if created:
            package.message_post(
                body=_('Package created from reception wizard (account: %s).') % self.account_id.display_name,
                message_type='comment',
            )
        else:
            package.message_post(
                body=_('Package updated from reception desk wizard.'),
                message_type='comment',
            )
        if self.with_incidence:
            package.message_post(
                body=_('Package marked with incident at reception.'),
                message_type='comment',
            )

    def _persist_reception_package(self):
        """Crea o actualiza el bulto con los valores del asistente y devuelve el registro."""
        self.ensure_one()
        if self.package_id:
            package = self.package_id.sudo()
            vals = self._package_vals_from_wizard()
            if self.with_incidence:
                vals['package_state'] = 'received'
                vals['package_has_incident'] = True
                vals = package._reception_package_location_vals_patch(vals)
                package.write(vals)
            else:
                if package.package_state in ('draft', 'received'):
                    vals['package_state'] = 'received'
                vals['package_has_incident'] = False
                vals = package._reception_package_location_vals_patch(vals)
                package.write(vals)
            self._post_reception_chatter(package, created=False)
            self._attach_wizard_media_to_package(package)
            return package
        Package = self.env['stock.quant.package'].sudo()
        vals = self._package_vals_from_wizard()
        if self.with_incidence:
            vals['package_state'] = 'received'
            vals['package_has_incident'] = True
            vals = Package._reception_package_location_vals_patch(vals)
            package = Package.create(vals)
        else:
            vals['package_state'] = 'received'
            vals['package_has_incident'] = False
            vals = Package._reception_package_location_vals_patch(vals)
            package = Package.create(vals)
        self._post_reception_chatter(package, created=True)
        self._attach_wizard_media_to_package(package)
        return package

    def _package_vals_from_wizard(self):
        self.ensure_one()
        vals = {
            'name': self.expedition1.strip(),
            'customer_reference': (self.expedition or '').strip() or False,
            'shipping_weight': self.weight,
            'packaging_length': self.length or 0.0,
            'width': self.width or 0.0,
            'height': self.height or 0.0,
            'carrier_id': self.carrier_id.id,
            'type': self.package_type,
            'sender_id': self.sender_id.id if self.sender_id else False,
        }
        return vals
