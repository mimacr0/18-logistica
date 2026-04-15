# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2026 DaFe Solutions
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import format_datetime

class StockQuantPackage(models.Model):
    _name = 'stock.quant.package'
    _inherit = ['stock.quant.package', 'mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    carrier_id = fields.Many2one('delivery.carrier', string='Carrier', tracking=True)
    sender_id = fields.Many2one('res.partner', string='Sender')
    shipping_address_id = fields.Many2one('res.partner', string='Shipping Address', domain="[('type', 'in', ['delivery', 'other', 'contact'])]")
    customer_reference = fields.Char(string='Customer Reference')
    number_of_packages = fields.Integer(string='Number of Packages', default=1)
    sale_id = fields.Many2one('sale.order', 'Pedido de Venta')
    type = fields.Selection([('return', 'Return Package'), ('new', 'New Package')], string='Type', default='new')
    package_state = fields.Selection(
        [
            ('draft', _('Waiting Package')),
            ('received', _('Received')),
            ('opened', _('Opened & Inspected')),
            ('done', _('Empty / Done')),
        ],
        string='Package status',
        default='draft',
        tracking=True,
    )
    package_has_incident = fields.Boolean(
        string='Package incident',
        default=False,
        tracking=True,
        help='Independent of package status: e.g. received with incident, or opened with incident.',
    )
    notes = fields.Text(string='Reception Notes')
    unpack_user_id = fields.Many2one('res.users', string='Unpacked by', readonly=True, copy=False, tracking=True, help='User who last completed an unpack operation (RMA or quant).')
    unpack_date = fields.Datetime(string='Unpacked on', readonly=True, copy=False, tracking=True, help='Date and time of the last unpack operation.')

    # Dimensions for the specific package instance
    height = fields.Float('Height', help="Packaging Height")
    width = fields.Float('Width', help="Packaging Width")
    packaging_length = fields.Float('Length', help="Packaging Length")
    
    # Optional image capturing from the web backend
    image_1920 = fields.Image(string="Photo of the package")
    
    # Units that were found inside this package
    rma_unit_ids = fields.One2many('rma.unit', 'package_id', string="RMA Units inside")
    package_products_line_ids = fields.One2many('rma.package.line', 'package_id', string='RMA Products')
    unpack_check_line_ids = fields.One2many(
        'rma.reception.check.line',
        'package_id',
        string='Reception unpack checks',
    )
    package_location_id = fields.Many2one(
        'stock.location',
        string='Package location',
        tracking=True,
        index=True,
        help='Logical location of the package in the reception flow (independent of the standard '
             'location computed from quants in the package).',
    )

    @api.model
    def _reception_default_package_location_customer_id(self):
        loc = self.env.ref('rma_inventory.stock_location_rma_customer_final', raise_if_not_found=False)
        return loc.id if loc else False

    @api.model
    def _reception_default_package_location_reception_id(self):
        loc = self.env.ref('rma_inventory.stock_location_rma_reception', raise_if_not_found=False)
        return loc.id if loc else False

    @api.model
    def _reception_default_package_location_unpack_id(self):
        loc = self.env.ref('rma_inventory.stock_location_rma_unpack_zone', raise_if_not_found=False)
        return loc.id if loc else False

    @api.model
    def _reception_package_location_vals_patch(self, vals):
        """Align package_location_id with package_state when XML locations exist."""
        vals = dict(vals or {})
        if 'package_state' not in vals:
            return vals
        st = vals['package_state']
        if st == 'received':
            lid = self._reception_default_package_location_reception_id()
            if lid:
                vals['package_location_id'] = lid
        elif st == 'opened':
            lid = self._reception_default_package_location_unpack_id()
            if lid:
                vals['package_location_id'] = lid
        return vals

    def _sync_reception_check_lines(self):
        """Fill checklist lines only the first time (package still has none).

        After that, the list is frozen: no new lines when templates change, no unlink when
        templates are archived or the package type changes.
        """
        Template = self.env['rma.reception.check.template']
        Line = self.env['rma.reception.check.line']
        for package in self:
            if package.unpack_check_line_ids:
                continue
            templates = Template._get_templates_for_package(package)
            for tmpl in templates:
                Line.create({
                    'package_id': package.id,
                    'template_id': tmpl.id,
                    'failed': False,
                })

    @api.model_create_multi
    def create(self, vals_list):
        cust_id = self._reception_default_package_location_customer_id()
        recv_id = self._reception_default_package_location_reception_id()
        unpack_id = self._reception_default_package_location_unpack_id()
        cleaned = []
        for vals in vals_list:
            v = dict(vals)
            if 'package_location_id' not in v:
                st = v.get('package_state')
                if st == 'received' and recv_id:
                    v['package_location_id'] = recv_id
                elif st == 'opened' and unpack_id:
                    v['package_location_id'] = unpack_id
                elif cust_id:
                    v['package_location_id'] = cust_id
            cleaned.append(v)
        records = super().create(cleaned)
        records._sync_reception_check_lines()
        return records

    def _reception_owner_partner(self):
        """res.partner owner of the package: package owner, quant owner, first line map, or RMA unit owner."""
        self.ensure_one()
        pack = self
        if 'owner_id' in pack._fields and pack.owner_id:
            return pack.owner_id
        quant = pack.quant_ids.filtered(lambda q: q.owner_id)[:1]
        if quant:
            return quant.owner_id
        line = pack.package_products_line_ids[:1]
        if line and line.product_map_id:
            return line.product_map_id.partner_id
        unit = pack.rma_unit_ids.filtered(lambda u: u.owner_id)[:1]
        if unit:
            return unit.owner_id
        return self.env['res.partner']

    @api.model
    def _reception_account_partner_id_from_partner(self, partner):
        """Resolve account.partner from res.partner (self, parent, commercial)."""
        if not partner:
            return False
        partner = self.env['res.partner'].sudo().browse(partner.id)
        if not partner.exists():
            return False
        seen = set()
        for p in (partner, partner.parent_id, partner.commercial_partner_id):
            if not p or p.id in seen:
                continue
            seen.add(p.id)
            if p.account_id:
                return p.account_id.id
        return False

    def _reception_default_account_partner_id(self):
        """Suggested account.partner for reception checks (from package owner chain)."""
        self.ensure_one()
        return self._reception_account_partner_id_from_partner(
            self._reception_owner_partner(),
        )

    def _reception_validate_confirm_prerequisites(
        self,
        account_partner_id,
        *,
        carrier_id=None,
        sender_id=None,
        shipping_weight=None,
        package_ref=None,
    ):
        """Shared rules before confirming reception (wizard or form).

        Optional kwargs use the transient wizard values when set; otherwise the package record.
        """
        self.ensure_one()
        if self.package_state != 'draft':
            raise UserError(
                _('Reception can only be confirmed when the package is in “Waiting Package” (draft) state.')
            )
        if not account_partner_id:
            raise ValidationError(_('Account is required.'))
        Carrier = self.env['delivery.carrier']
        if carrier_id is not None:
            if not carrier_id or not Carrier.browse(carrier_id).exists():
                raise ValidationError(_('Carrier is required.'))
        elif not self.carrier_id:
            raise ValidationError(_('Carrier is required.'))
        Partner = self.env['res.partner']
        if sender_id is not None:
            if not sender_id or not Partner.browse(sender_id).exists():
                raise ValidationError(_('Sender is required.'))
        elif not self.sender_id:
            raise ValidationError(_('Sender is required.'))
        lines_with_map = self.package_products_line_ids.filtered(lambda l: l.product_map_id)
        if not lines_with_map:
            raise ValidationError(
                _('Add at least one declared product line with a product mapping (product map) before confirming.')
            )
        sw = self.shipping_weight if shipping_weight is None else shipping_weight
        if not sw or sw <= 0:
            raise ValidationError(_('Shipping weight must be greater than zero.'))
        ref = (self.name or '').strip() if package_ref is None else (package_ref or '').strip()
        if not ref:
            raise ValidationError(_('Package reference / tracking is required.'))

    def action_confirm_reception_from_form(self):
        """Confirm reception from the package form (draft → received) without opening the wizard."""
        self.ensure_one()
        self._reception_validate_confirm_prerequisites(self._reception_default_account_partner_id())
        wvals = self._reception_package_location_vals_patch({
            'package_state': 'received',
            'package_has_incident': False,
        })
        self.write(wvals)
        self.message_post(
            body=_('Reception confirmed from package form.'),
            message_type='comment',
        )
        return True

    def action_finish_reception_closed(self):
        """Close reception workflow: state done; package_has_incident is left unchanged; form no longer editable."""
        self.ensure_one()
        if self.package_state != 'opened':
            raise UserError(
                _('You can only finish reception when the package is unpacked (status Opened & inspected).')
            )
        had_incident = self.package_has_incident
        self.write({'package_state': 'done'})
        if had_incident:
            body = _(
                'Reception closed — incident flag left set for traceability. Status: empty / done (record locked).'
            )
        else:
            body = _('Reception finished. Package status: empty / done (record locked).')
        self.message_post(body=body, message_type='comment')
        return True

    def _log_unpack_operation(self):
        """Record who unpacked and when; post a note in the chatter."""
        self.ensure_one()
        now = fields.Datetime.now()
        self.write({
            'unpack_user_id': self.env.user.id,
            'unpack_date': now,
        })
        when_str = format_datetime(self.env, now, dt_format='short')
        self.message_post(
            body=_('Package unpacked by %(user)s on %(when)s.') % {
                'user': self.env.user.name,
                'when': when_str,
            },
        )

    def _desk_apply_unpack_check_selection(self, desk_line_ids):
        """Set failed on checklist lines from mesa unpack detail (ids must belong to this package)."""
        self.ensure_one()
        lines = self.unpack_check_line_ids
        id_set = {int(x) for x in (desk_line_ids or [])}
        allowed = set(lines.ids)
        if not id_set <= allowed:
            raise UserError(_('Invalid reception check line selection for this package.'))
        for line in lines:
            line.failed = line.id in id_set

    def _unpack_validate_reception_checks(self):
        """Sync checklist; require templates; mesa detail sends explicit selection, else block on any failed."""
        self.ensure_one()
        self._sync_reception_check_lines()
        if not self.unpack_check_line_ids:
            raise UserError(
                _('No checklist items are configured. Add templates or contact an administrator.')
            )
        lines = self.unpack_check_line_ids
        desk_payload = self.env.context.get('desk_unpack_incident_line_ids')
        if desk_payload is not None:
            self._desk_apply_unpack_check_selection(desk_payload)
            return
        if any(lines.mapped('failed')):
            raise UserError(
                _('No check may be marked as failed to continue, or use “Report unpack incident”.')
            )

    def _finalize_open_after_reception_unpack(self):
        """opened + package_has_incident from failed checks; chatter for unpack and optional incident summary."""
        self.ensure_one()
        has_inc = any(self.unpack_check_line_ids.mapped('failed'))
        now = fields.Datetime.now()
        wvals = self._reception_package_location_vals_patch({
            'package_state': 'opened',
            'package_has_incident': has_inc,
            'unpack_user_id': self.env.user.id,
            'unpack_date': now,
        })
        self.write(wvals)
        if has_inc:
            failed = self.unpack_check_line_ids.filtered('failed')
            parts = ['• %s' % line.template_id.name for line in failed]
            body = _('Unpack completed — reception checks marked as incident:\n%s') % (
                '\n'.join(parts) if parts else _('(none)'),
            )
            self.message_post(body=body, message_type='comment')
        when_str = format_datetime(self.env, now, dt_format='short')
        self.message_post(
            body=_('Package unpacked by %(user)s on %(when)s.') % {
                'user': self.env.user.name,
                'when': when_str,
            },
        )

    def unpack(self):
        """Standard stock unpack: also store unpack user/date when quants are moved out."""
        packages_to_trace = self.filtered(lambda p: p.quant_ids)
        super().unpack()
        for package in packages_to_trace:
            package._log_unpack_operation()

    def _get_lines_to_unpack(self):
        """Return declared lines still pending unpack (`unpacked` True) for the whole package."""
        self.ensure_one()
        lines = self.package_products_line_ids.filtered(lambda l: l.unpacked)
        if not lines:
            return None, {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Info'),
                    'message': _('Nothing to unpack.'),
                    'type': 'warning',
                    'sticky': False,
                }
            }
        return lines, None

    def _reception_unpack_success_client_action(self):
        """Notificación de éxito; en mesa de recepción encadena reinicio + cierre del modal."""
        self.ensure_one()
        close = {'type': 'ir.actions.act_window_close'}
        params = {
            'title': _('Success'),
            'message': _('All items unpacked successfully.'),
            'type': 'success',
        }
        if self.env.context.get('package_reception_desk'):
            params['next'] = {
                'type': 'ir.actions.client',
                'tag': 'rma_reception.clear_desk_search',
                'params': {
                    'desk': True,
                    'next': close,
                },
            }
        elif self.env.context.get('package_unpack_desk') and (
            (self.type == 'return' and self.rma_unit_ids)
            or self.quant_ids.filtered(lambda q: q.quantity > 0)
        ):
            params['next'] = {
                'type': 'ir.actions.client',
                'tag': 'rma_reception.unpack_desk_post_unpack',
                'params': {'package_id': self.id},
            }
        else:
            params['next'] = close
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': params,
        }

    def _unpack_desk_rma_units(self):
        """Unidades del bulto aún en recepción operativa (pendientes de triage en la mesa)."""
        self.ensure_one()
        return self.rma_unit_ids.filtered(lambda u: u.active and u.state == 'received')

    def action_unpack_desk_move_to_review(self):
        self.ensure_one()
        units = self._unpack_desk_rma_units()
        if not units:
            raise UserError(
                _('No RMA units in “Received” state remain on this package.')
            )
        units.action_rma_to_review()
        return True

    def action_unpack_desk_move_to_repair(self):
        self.ensure_one()
        units = self._unpack_desk_rma_units()
        if not units:
            raise UserError(
                _('No RMA units in “Received” state remain on this package.')
            )
        units.action_rma_to_repair()
        return True

    def _unpack_desk_default_store_location_id(self):
        loc = self.env.ref('rma_inventory.stock_location_rma_staging', raise_if_not_found=False)
        if loc:
            return loc.id
        return self.env.ref('stock.stock_location_stock').id

    def _action_unpack_desk_store_wizard_vals(self, rma_units, quants):
        """Build create vals for rma.reception.desk.store.wizard from recordsets."""
        self.ensure_one()
        loc_id = self._unpack_desk_default_store_location_id()
        line_cmds = []
        for u in rma_units:
            line_cmds.append(
                (
                    0,
                    0,
                    {
                        'line_type': 'rma_unit',
                        'rma_unit_id': u.id,
                        'location_id': loc_id,
                    },
                )
            )
        for q in quants:
            line_cmds.append(
                (
                    0,
                    0,
                    {
                        'line_type': 'quant',
                        'quant_id': q.id,
                        'location_id': loc_id,
                    },
                )
            )
        return {'package_id': self.id, 'line_ids': line_cmds}

    def action_unpack_desk_open_store_wizard_rma(self):
        """Choose internal location per RMA unit (context: desk_store_rma_unit_ids=list, optional)."""
        self.ensure_one()
        units = self._unpack_desk_rma_units()
        ids_filter = self.env.context.get('desk_store_rma_unit_ids')
        if ids_filter:
            units = units.filtered(lambda u: u.id in tuple(ids_filter))
        if not units:
            raise UserError(
                _('No RMA units in “Received” state to store for this package.')
            )
        vals = self._action_unpack_desk_store_wizard_vals(units, self.env['stock.quant'].browse())
        wiz = self.env['rma.reception.desk.store.wizard'].create(vals)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Almacenar — elegir ubicaciones'),
            'res_model': 'rma.reception.desk.store.wizard',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'res_id': wiz.id,
            'target': 'new',
            'context': self.env.context,
        }

    def action_unpack_desk_open_store_wizard_quants(self):
        """Choose internal location per stock.quant (context: desk_store_quant_ids=list, optional)."""
        self.ensure_one()
        quants = self.quant_ids.filtered(lambda q: q.quantity > 0)
        ids_filter = self.env.context.get('desk_store_quant_ids')
        if ids_filter:
            quants = quants.filtered(lambda q: q.id in tuple(ids_filter))
        if not quants:
            raise UserError(_('No stock quants with quantity on this package to store.'))
        vals = self._action_unpack_desk_store_wizard_vals(self.env['rma.unit'].browse(), quants)
        wiz = self.env['rma.reception.desk.store.wizard'].create(vals)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Almacenar quants — elegir ubicaciones'),
            'res_model': 'rma.reception.desk.store.wizard',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'res_id': wiz.id,
            'target': 'new',
            'context': self.env.context,
        }

    def action_unpack_desk_move_to_storage(self):
        """Open wizard to pick an internal location per RMA unit still in “Received” (send all from desk)."""
        return self.action_unpack_desk_open_store_wizard_rma()

    def action_unpack_desk_move_to_scrap(self):
        self.ensure_one()
        units = self._unpack_desk_rma_units()
        if not units:
            raise UserError(
                _('No RMA units in “Received” state remain on this package.')
            )
        units.action_rma_to_scrap()
        return True

    def action_open_reception_confirm_wizard(self):
        """Open the reception wizard to confirm the package (draft → received; incident is a separate flag)."""
        self.ensure_one()
        view = self.env.ref(
            'rma_reception.view_rma_reception_package_wizard_form_desk',
            raise_if_not_found=False,
        )
        return {
            'type': 'ir.actions.act_window',
            'name': _('Confirm reception'),
            'res_model': 'rma.reception.package.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_package_id': self.id},
            'views': [(view.id, 'form')] if view else [(False, 'form')],
        }

    def action_unpack_rma(self):
        """Validate reception checks on the package, then create RMA units."""
        self.ensure_one()
        if self.type != 'return':
            return False
        _lines, warning = self._get_lines_to_unpack()
        if warning:
            return warning
        self._unpack_validate_reception_checks()
        ctx = {}
        if self.env.context.get('package_unpack_desk'):
            ctx['package_unpack_desk'] = True
        return self.with_context(**ctx)._execute_rma_unpack_after_checks()

    def _execute_rma_unpack_after_checks(self):
        """Create rma.unit records after reception checks (wizard or mesa)."""
        self.ensure_one()
        if self.type != 'return':
            return False

        lines_to_unpack, warning = self._get_lines_to_unpack()
        if warning:
            return warning

        reception_loc = self.env.ref('rma_inventory.stock_location_rma_reception', raise_if_not_found=False)
        fallback_loc = self.location_id.id or self.env.ref('stock.stock_location_stock').id
        recv_loc = reception_loc.id if reception_loc else fallback_loc
        units_to_create = []
        for line in lines_to_unpack:
            for _unit_idx in range(line.received_qty):
                units_to_create.append({
                    'package_id': self.id,
                    'account_product_map_id': line.product_map_id.id,
                    'state': 'received',
                    'condition': 'E',
                    'location_id': recv_loc,
                })

        lines_to_unpack.write({'unpacked': False})
        if units_to_create:
            self.env['rma.unit'].create(units_to_create)

        self._finalize_open_after_reception_unpack()

        return self._reception_unpack_success_client_action()

    def action_unpack_quant(self):
        """Validate reception checks on the package, then create stock quants."""
        self.ensure_one()
        if self.type != 'new':
            return False
        _lines, warning = self._get_lines_to_unpack()
        if warning:
            return warning
        self._unpack_validate_reception_checks()
        ctx = {}
        if self.env.context.get('package_unpack_desk'):
            ctx['package_unpack_desk'] = True
        return self.with_context(**ctx)._execute_quant_unpack_after_checks()

    def action_report_unpack_incident(self):
        """Post chatter note and set package_has_incident when checks are not all OK (state stays received)."""
        self.ensure_one()
        self._sync_reception_check_lines()
        if not self.unpack_check_line_ids:
            raise UserError(
                _('No checklist items are configured. Add templates or contact an administrator.')
            )
        lines = self.unpack_check_line_ids
        if lines and not any(lines.mapped('failed')):
            raise UserError(
                _('No failures are marked. Unpack the package or mark a failed check to report an incident.')
            )
        failed = lines.filtered(lambda l: l.failed)
        parts = ['• %s' % line.template_id.name for line in failed]
        body = _('Incident at reception — unpack stopped.\n\nFailed checks:\n%s') % (
            '\n'.join(parts) if parts else _('(none)'),
        )
        self.write({'package_has_incident': True})
        self.message_post(body=body, message_type='comment')
        return True

    def _execute_quant_unpack_after_checks(self):
        """Create stock.quant records after reception checks (wizard or mesa)."""
        self.ensure_one()
        if self.type != 'new':
            return False

        lines_to_unpack, warning = self._get_lines_to_unpack()
        if warning:
            return warning

        quants_to_create = []
        for line in lines_to_unpack:
            if line.received_qty <= 0:
                continue
            quants_to_create.append({
                'product_id': line.product_map_id.product_id.id,
                'location_id': self.location_id.id or self.env.ref('stock.stock_location_stock').id,
                'package_id': self.id,
                'quantity': line.received_qty,
                'owner_id': line.product_map_id.account_id.partner_id.id,
                'account_product_map_id': line.product_map_id.id,
            })

        lines_to_unpack.write({'unpacked': False})

        if quants_to_create:
            self.env['stock.quant'].create(quants_to_create)

        self._finalize_open_after_reception_unpack()

        return self._reception_unpack_success_client_action()

