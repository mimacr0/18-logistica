# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2026 DaFe Solutions
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero


class RmaUnit(models.Model):
    _name = 'rma.unit'
    _description = 'RMA Unit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'

    @api.model_create_multi
    def create(self, vals_list):
        Map = self.env['account.product.map']
        cleaned = []
        for vals in vals_list:
            vals = dict(vals)
            if vals.get('account_product_map_id'):
                vals.pop('product_id', None)
                vals.pop('owner_id', None)
            else:
                pid = vals.pop('product_id', None)
                oid = vals.pop('owner_id', None)
                if pid is not None and pid is not False:
                    pid = pid.id if isinstance(pid, models.BaseModel) else pid
                if oid is not None and oid is not False:
                    oid = oid.id if isinstance(oid, models.BaseModel) else oid
                if pid and oid:
                    pmap = Map.search([
                        ('product_id', '=', int(pid)),
                        ('partner_id', '=', int(oid)),
                        ('active', '=', True),
                    ], limit=1)
                    if pmap:
                        vals['account_product_map_id'] = pmap.id
            if not vals.get('account_product_map_id'):
                raise ValidationError(_('Each RMA unit must reference an account product mapping.'))
            if vals.get('name', _('RMA...')) == _('RMA...'):
                vals['name'] = self.env['ir.sequence'].next_by_code('rma.unit.sequence') or _('RMA...')
            cleaned.append(vals)
        records = super().create(cleaned)
        now = fields.Datetime.now()
        reason = self.env.context.get('rma_transition_reason') or _('Creation')
        move_vals = []
        for record in records:
            move_vals.append({
                'rma_unit_id': record.id,
                'from_location_id': False,
                'to_location_id': record.location_id.id if record.location_id else False,
                'from_state': False,
                'to_state': record.state,
                'user_id': self.env.user.id,
                'date': now,
                'reason': reason,
            })
        self.env['rma.unit.move'].create(move_vals)
        to_date = records.filtered(lambda r: r.state == 'received' and not r.received_date)
        if to_date:
            to_date.with_context(skip_rma_unit_move_logging=True).write({'received_date': now})
        return records

    def write(self, vals):
        vals = dict(vals)
        vals.pop('product_id', None)
        vals.pop('owner_id', None)
        if self.env.context.get('skip_rma_unit_move_logging'):
            return super().write(vals)
        if 'state' not in vals and 'location_id' not in vals:
            return super().write(vals)
        return self._rma_unit_write_with_move_logging(vals)

    def _rma_unit_write_with_move_logging(self, vals):
        """Escribe ``vals`` (state y/o location) y registra ``rma.unit.move`` + fechas de hito si aplica."""
        track_state = 'state' in vals
        track_loc = 'location_id' in vals
        reason = self.env.context.get('rma_transition_reason') or _('Status / location update')
        move_vals_list = []
        for rec in self:
            old_state = rec.state
            old_loc = rec.location_id.id if rec.location_id else False
            new_state = vals['state'] if track_state else old_state
            new_loc = vals['location_id'] if track_loc else old_loc
            if track_loc and vals.get('location_id') is False:
                new_loc = False
            if new_state == old_state and new_loc == old_loc:
                continue
            move_vals_list.append({
                'rma_unit_id': rec.id,
                'from_location_id': old_loc or False,
                'to_location_id': new_loc if new_loc else False,
                'from_state': old_state or False,
                'to_state': new_state or False,
                'user_id': self.env.user.id,
                'date': fields.Datetime.now(),
                'reason': reason,
            })
        res = super().write(vals)
        if move_vals_list:
            self.env['rma.unit.move'].create(move_vals_list)
        if track_state and vals.get('state'):
            now = fields.Datetime.now()
            date_field = {
                'received': 'received_date',
                'stored': 'stored_date',
                'shipped': 'shipped_date',
            }.get(vals['state'])
            if date_field:
                self.with_context(skip_rma_unit_move_logging=True).write({date_field: now})
        return res

    def _rma_ref_location(self, xmlid):
        loc = self.env.ref(xmlid, raise_if_not_found=False)
        return loc.id if loc else False

    def _rma_require_location(self, xmlid, label):
        loc_id = self._rma_ref_location(xmlid)
        if not loc_id:
            raise UserError(
                _('The stock location "%s" is missing. Update module RMA Inventory (data: %s).')
                % (label, xmlid)
            )
        return loc_id

    def action_rma_to_reception(self):
        loc_id = self._rma_require_location('rma_inventory.stock_location_rma_reception', _('RMA reception'))
        self.with_context(rma_transition_reason=_('To reception')).write({
            'state': 'received',
            'location_id': loc_id,
        })
        return True

    def action_rma_to_review(self):
        loc_id = self._rma_require_location('rma_inventory.stock_location_rma_review', _('RMA review'))
        self.with_context(rma_transition_reason=_('To review')).write({
            'state': 'review',
            'location_id': loc_id,
        })
        return True


    # TODO: this action will be updated when the repair workflow is implemented what it should do is an inherit from the repair workflow
    # el método heredado debe crear la reparación, pero se debe llamar a este método para que cambie el estado a repair u creee el movimiento de la unidad
    def action_rma_to_repair(self):
        loc_id = self._rma_require_location('rma_inventory.stock_location_rma_repair', _('RMA repair'))
        self.with_context(rma_transition_reason=_('To repair')).write({
            'state': 'repair',
            'location_id': loc_id,
        })
        return True

    def action_rma_to_shipped(self):
        loc_id = self._rma_require_location('rma_inventory.stock_location_rma_shipped', _('RMA shipped'))
        self.with_context(rma_transition_reason=_('Shipped')).write({
            'state': 'shipped',
            'location_id': loc_id,
        })
        return True

    def action_rma_to_staging_storage(self):
        """Ubicación RMA / Almacén provisional (atajo frente al asistente de almacenaje)."""
        if not self:
            raise UserError(_('Select at least one RMA unit.'))
        loc_id = self._rma_require_location(
            'rma_inventory.stock_location_rma_staging',
            _('RMA provisional storage'),
        )
        self.with_context(rma_transition_reason=_('To storage')).write({
            'state': 'stored',
            'location_id': loc_id,
        })
        return True

    def action_rma_to_scrap(self):
        """Ubicación de chatarra de la compañía + estado almacenado y condición descarte."""
        if not self:
            raise UserError(_('Select at least one RMA unit.'))
        scrap_loc = self.env['stock.location'].search([
            ('scrap_location', '=', True),
            ('company_id', 'in', [False, self.env.company.id]),
        ], limit=1)
        if not scrap_loc:
            raise UserError(
                _('No scrap location is configured. Mark a stock location as “Is a Scrap Location?”.')
            )
        self.with_context(rma_transition_reason=_('To scrap')).write({
            'state': 'stored',
            'location_id': scrap_loc.id,
            'condition': 'D',
        })
        return True

    def action_rma_open_store_wizard(self):
        if not self:
            raise UserError(_('Select at least one RMA unit.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Store RMA units'),
            'res_model': 'rma.unit.store.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': dict(self.env.context, default_rma_unit_ids=[(6, 0, self.ids)]),
        }

    def action_view_rma_moves(self):
        """Abrir movimientos de la(s) unidad(es) seleccionada(s)."""
        if not self:
            return False
        action = self.env.ref('rma_inventory.action_rma_unit_move').read()[0]
        action['domain'] = [('rma_unit_id', 'in', self.ids)]
        if len(self) == 1:
            action['context'] = dict(self.env.context, default_rma_unit_id=self.id)
        else:
            action['context'] = dict(self.env.context)
        return action

    def action_print_name(self):
        """Genera un PDF con el nombre (número RMA) en grande."""
        return self.env.ref('rma_inventory.action_report_rma_unit_name').report_action(self)

    def action_open_move_desk_wizard_multi(self):
        """Lista RMA: requiere active_ids (selección múltiple)."""
        ids = self.env.context.get('active_ids') or []
        if not ids:
            raise UserError(_('Seleccione al menos una unidad RMA en la lista.'))
        return self.env['rma.unit'].action_move_desk_prepare_wizard(ids)

    @api.model
    def action_move_desk_prepare_wizard(self, unit_ids):
        """Crea el asistente de movimiento con origen por unidad y destino editable (registra rma.unit.move al confirmar)."""
        if not unit_ids:
            raise UserError(_('Seleccione al menos una unidad RMA.'))
        raw_ids = list(dict.fromkeys(int(i) for i in unit_ids))
        units = self.browse(raw_ids).filtered('active')
        if not units:
            raise UserError(_('No hay unidades RMA activas entre las seleccionadas.'))
        staging = self.env.ref('rma_inventory.stock_location_rma_staging', raise_if_not_found=False)
        if staging:
            default_dest = staging.id
        else:
            default_dest = self.env.ref('stock.stock_location_stock').id
        line_cmds = []
        for u in units:
            line_cmds.append(
                (
                    0,
                    0,
                    {
                        'rma_unit_id': u.id,
                        'to_location_id': default_dest,
                    },
                )
            )
        wiz = self.env['rma.unit.move.desk.wizard'].create({
            'location_dest_id': default_dest,
            'line_ids': line_cmds,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Mover unidades RMA'),
            'res_model': 'rma.unit.move.desk.wizard',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'res_id': wiz.id,
            'target': 'new',
            'context': self.env.context,
        }

    @api.model
    def _move_desk_storage_category_domain(self):
        """Dominio extra para ubicaciones en la mesa RMA según categorías de almacenamiento de la compañía.

        - Sin «incluir»: no se restringe por categoría.
        - Con «incluir»: solo ubicaciones con ``storage_category_id`` en la lista (sin categoría → excluidas).
        - Sin «excluir»: no se excluye por categoría.
        - Con «excluir»: se excluyen ubicaciones cuya categoría está en la lista.
        """
        company = self.env.company
        domain = []
        inc = company.rma_move_desk_storage_category_include_ids
        exc = company.rma_move_desk_storage_category_exclude_ids
        if inc:
            domain.append(('storage_category_id', 'in', inc.ids))
        if exc:
            domain.append(('storage_category_id', 'not in', exc.ids))
        return domain

    @api.model
    def _move_desk_root_locations(self):
        """Recordset ordenado: ajustes (m2m), parámetro (ids separados por coma), NV1/Stock o Stock."""
        Location = self.env['stock.location']
        Location.check_access_rights('read')
        company = self.env.company
        configured = company.rma_move_desk_root_location_ids
        if configured:
            return configured
        param = self.env['ir.config_parameter'].sudo().get_param(
            'rma_inventory.move_desk_root_location_id'
        )
        if param:
            ids = []
            for part in str(param).split(','):
                part = part.strip()
                if part.isdigit():
                    ids.append(int(part))
            if ids:
                locs = Location.browse(ids).exists()
                ordered_ids = [lid for lid in ids if lid in locs.ids]
                if ordered_ids:
                    return Location.browse(ordered_ids)
        loc = Location.search([('complete_name', 'ilike', 'NV1/Stock')], limit=1)
        if loc:
            return loc
        loc = self.env.ref('stock.stock_location_stock', raise_if_not_found=False)
        return loc if loc else Location

    @api.model
    def move_desk_get_root_locations(self):
        """Lista de raíces con el mismo formato que las celdas del selector (incl. has_children)."""
        roots = self._move_desk_root_locations()
        cat_domain = self._move_desk_storage_category_domain()
        if cat_domain:
            roots = roots.filtered_domain(cat_domain)
        if not roots:
            raise UserError(
                _(
                    'No se encuentra ninguna ubicación raíz del selector. En Ajustes → Inventario → RMA, '
                    'defina «Raíces del selector», o use una ubicación cuya ruta contenga «NV1/Stock», '
                    'o el parámetro rma_inventory.move_desk_root_location_id (uno o varios ids separados por coma). '
                    'Revise también los filtros de categorías de almacenamiento (incluir/excluir).'
                )
            )
        Location = self.env['stock.location']
        result = []
        for loc in roots:
            sub_domain = [
                ('location_id', '=', loc.id),
                ('active', '=', True),
                ('usage', 'in', ('internal', 'view', 'transit')),
            ] + cat_domain
            sub_count = Location.search_count(sub_domain)
            result.append(
                {
                    'id': loc.id,
                    'name': loc.name,
                    'display_name': loc.display_name,
                    'complete_name': loc.complete_name,
                    'usage': loc.usage,
                    'has_children': bool(sub_count),
                }
            )
        return result

    @api.model
    def move_desk_location_children(self, parent_id):
        """Hijos directos de una ubicación para la matriz de botones (internal / view)."""
        Location = self.env['stock.location']
        Location.check_access_rights('read')
        parent = Location.browse(int(parent_id))
        if not parent.exists():
            return []
        cat_domain = self._move_desk_storage_category_domain()
        children = Location.search(
            [
                ('location_id', '=', parent.id),
                ('active', '=', True),
                ('usage', 'in', ('internal', 'view', 'transit')),
            ]
            + cat_domain,
            order='complete_name, id',
        )
        result = []
        for c in children:
            sub_domain = [
                ('location_id', '=', c.id),
                ('active', '=', True),
                ('usage', 'in', ('internal', 'view', 'transit')),
            ] + cat_domain
            sub_count = Location.search_count(sub_domain)
            result.append(
                {
                    'id': c.id,
                    'name': c.name,
                    'display_name': c.display_name,
                    'has_children': bool(sub_count),
                    'usage': c.usage,
                }
            )
        return result

    @api.model
    def move_desk_suggest_locations_by_maps(self, rma_unit_ids=None, quant_ids=None):
        """Ubicaciones internas donde ya hay stock.quant o rma.unit con alguno de los mapas de las líneas."""
        rma_unit_ids = [int(x) for x in (rma_unit_ids or []) if x is not None]
        quant_ids = [int(x) for x in (quant_ids or []) if x is not None]
        Rma = self.env['rma.unit']
        Quant = self.env['stock.quant']
        Location = self.env['stock.location']
        Rma.check_access_rights('read')
        Quant.check_access_rights('read')
        Location.check_access_rights('read')

        map_ids = set()
        for unit in Rma.browse(rma_unit_ids).exists():
            if unit.account_product_map_id:
                map_ids.add(unit.account_product_map_id.id)
        for quant in Quant.browse(quant_ids).exists():
            if quant.account_product_map_id:
                map_ids.add(quant.account_product_map_id.id)
        if not map_ids:
            return []

        map_ids = list(map_ids)
        loc_ids = set()

        quants = Quant.search(
            [
                ('quantity', '>', 0),
                ('account_product_map_id', 'in', map_ids),
                ('location_id.usage', '=', 'internal'),
            ]
        )
        for q in quants:
            rounding = q.product_uom_id.rounding
            if float_compare(q.available_quantity, 0, precision_rounding=rounding) > 0:
                loc_ids.add(q.location_id.id)

        units = Rma.search(
            [
                ('active', '=', True),
                ('account_product_map_id', 'in', map_ids),
                ('location_id', '!=', False),
                ('location_id.usage', '=', 'internal'),
            ]
        )
        for u in units:
            loc_ids.add(u.location_id.id)

        if not loc_ids:
            return []

        locations = Location.browse(sorted(loc_ids)).exists()
        cat_domain = self._move_desk_storage_category_domain()
        if cat_domain:
            locations = locations.filtered_domain(cat_domain)
        locations = locations.sorted(lambda loc: (loc.complete_name or '', loc.id))
        return [
            {
                'id': loc.id,
                'name': loc.name,
                'display_name': loc.display_name,
                'complete_name': loc.complete_name,
                'usage': loc.usage,
                'has_children': False,
            }
            for loc in locations
        ]

    def _move_desk_validate_destination_location(self, location_id):
        if not location_id:
            raise UserError(_('Seleccione una ubicación de destino.'))
        Location = self.env['stock.location']
        Location.check_access_rights('read')
        loc = Location.browse(int(location_id))
        if not loc.exists():
            raise UserError(_('La ubicación de destino no existe.'))
        if loc.usage != 'internal':
            raise UserError(
                _('La ubicación de destino debe ser de tipo interno (almacenaje), no una ubicación vista.')
            )
        cat_domain = self._move_desk_storage_category_domain()
        if cat_domain and not loc.filtered_domain(cat_domain):
            raise UserError(
                _(
                    'La ubicación de destino no cumple los filtros de categoría de almacenamiento '
                    'de la mesa RMA (incluir/excluir en Ajustes → Inventario → RMA).'
                )
            )
        return loc

    @api.model
    def _move_desk_map_and_account_partner_json(self, map_record):
        """Payload JSON para mesa: mapa cliente (account.product.map) y cuenta (account.partner)."""
        if not map_record:
            return {
                'account_product_map': False,
                'account_partner': False,
            }
        acc = map_record.account_id
        return {
            'account_product_map': {
                'id': map_record.id,
                'display_name': map_record.display_name,
            },
            'account_partner': {
                'id': acc.id,
                'display_name': acc.display_name,
            }
            if acc
            else False,
        }

    @api.model
    def move_desk_apply_mixed(self, location_id, rma_unit_ids=None, quant_lines=None):
        """Mueve unidades RMA y/o cantidades parciales de quants a la misma ubicación interna.

        :param quant_lines: lista de dicts ``{'quant_id': int, 'quantity': float}``.
        :return: dict con ``ok``, ubicación destino, y por cada ítem movido el mapa y ``account.partner``.
        """
        rma_unit_ids = list(rma_unit_ids or [])
        quant_lines = list(quant_lines or [])
        if not rma_unit_ids and not quant_lines:
            raise UserError(_('No hay líneas que mover.'))
        loc = self._move_desk_validate_destination_location(location_id)

        result = {
            'ok': True,
            'location_id': [loc.id, loc.display_name],
            'rma_units': [],
            'quant_moves': [],
        }

        if rma_unit_ids:
            raw_ids = list(dict.fromkeys(int(i) for i in rma_unit_ids))
            units = self.browse(raw_ids).filtered('active')
            if not units:
                raise UserError(_('No hay unidades RMA activas.'))
            units.with_context(rma_transition_reason=_('Move desk')).write({'location_id': loc.id})
            for unit in units:
                row = {
                    'id': unit.id,
                    'display_name': unit.display_name,
                }
                row.update(self._move_desk_map_and_account_partner_json(unit.account_product_map_id))
                result['rma_units'].append(row)

        if not quant_lines:
            return result

        Quant = self.env['stock.quant']
        Move = self.env['stock.move']
        Quant.check_access_rights('read')
        Move.check_access_rights('create')
        inv_ctx = dict(self.env.context, inventory_name=_('Move desk'))

        for ql in quant_lines:
            if not isinstance(ql, dict):
                continue
            qid = int(ql.get('quant_id') or 0)
            qty = float(ql.get('quantity') or 0.0)
            quant = Quant.browse(qid)
            if not quant.exists():
                raise UserError(_('Una línea de stock indicada ya no existe.'))
            rounding = quant.product_uom_id.rounding
            if float_is_zero(qty, precision_rounding=rounding):
                raise UserError(
                    _('La cantidad a mover debe ser mayor que cero (%s).') % quant.product_id.display_name
                )
            available = quant.available_quantity
            if float_compare(qty, available, precision_rounding=rounding) > 0:
                raise UserError(
                    _(
                        'La cantidad %(qty)s supera la disponible %(avail)s para %(prod)s en %(loc)s.'
                    )
                    % {
                        'qty': qty,
                        'avail': available,
                        'prod': quant.product_id.display_name,
                        'loc': quant.location_id.display_name,
                    }
                )
            if quant.location_id == loc:
                continue
            if quant.location_id.usage != 'internal':
                raise UserError(
                    _('Solo se pueden mover quants desde ubicaciones internas (%s).')
                    % quant.product_id.display_name
                )
            move_vals = quant.with_context(**inv_ctx)._get_inventory_move_values(
                qty,
                quant.location_id,
                loc,
                quant.package_id,
                False,
            )
            move = Move.create(move_vals)
            move._action_done()
            qrow = {
                'quant_id': quant.id,
                'quantity': qty,
                'product_display_name': quant.product_id.display_name,
            }
            qrow.update(self._move_desk_map_and_account_partner_json(quant.account_product_map_id))
            result['quant_moves'].append(qrow)

        return result

    @api.model
    def move_desk_apply_destination(self, unit_ids, location_id):
        """Compatibilidad: solo unidades RMA (delega en ``move_desk_apply_mixed``)."""
        if not unit_ids:
            raise UserError(_('No hay unidades RMA.'))
        return self.move_desk_apply_mixed(location_id, list(unit_ids or []), [])

    @api.constrains('account_product_map_id')
    def _check_account_product_map_id(self):
        if self.env.context.get('skip_rma_unit_map_constraint'):
            return
        for rec in self:
            if not rec.account_product_map_id:
                raise ValidationError(_('Product mapping is required on RMA units.'))

    name = fields.Char(
        string='RMA Number',
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _('RMA...'),
    )
    active = fields.Boolean(default=True, string='Active')
    account_product_map_id = fields.Many2one(
        'account.product.map',
        string='Product mapping',
        required=True,
        ondelete='restrict',
        index=True,
        tracking=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Internal product',
        related='account_product_map_id.product_id',
        store=True,
        readonly=True,
        index=True,
    )
    owner_id = fields.Many2one(
        'res.partner',
        string='Owner',
        related='account_product_map_id.partner_id',
        store=True,
        readonly=True,
        tracking=True,
    )
    package_id = fields.Many2one('stock.quant.package', string='Package')
    location_id = fields.Many2one('stock.location', index=True, string='Location', tracking=True)
    # Identifiers from account.product.map (client / catalog)
    account_sku = fields.Char(
        related='account_product_map_id.account_sku',
        string='Account SKU',
        readonly=True,
        store=True,
    )
    account_ean13 = fields.Char(
        related='account_product_map_id.account_ean13',
        string='EAN13',
        readonly=True,
        store=True,
    )
    account_fnsku = fields.Char(
        related='account_product_map_id.account_fnsku',
        string='FNSKU',
        readonly=True,
        store=True,
    )
    account_asin = fields.Char(
        related='account_product_map_id.account_asin',
        string='ASIN',
        readonly=True,
        store=True,
    )
    marketplace = fields.Selection(
        [
            ('amazon', 'Amazon'),
            ('cdiscount', 'Cdiscount'),
            ('ebay', 'eBay'),
            ('temu', 'Temu'),
            ('aliexpress', 'AliExpress'),
            ('pccomponentes', 'PcComponentes'),
            ('carrefour', 'Carrefour'),
            ('worten', 'Worten'),
            ('web', 'Webstore'),
            ('other', 'Other'),
        ],
        string='Marketplace',
        index=True,
        tracking=True,
    )
    # Identifiers for this physical unit (instance)
    serial = fields.Char(index=True, string='Serial')
    imei = fields.Char(index=True, string='IMEI')
    condition = fields.Selection(
        [
            ('E', 'On hold'),
            ('A', 'New'),
            ('B', 'Used'),
            ('C', 'Repair'),
            ('D', 'Discard'),
            ('converted_to_spare_parts', 'Converted to Spare Parts'),
        ],
        string=_('Physical condition'),
        tracking=True,
        help=_(
            'Internal classification of how the physical product is (grading). '
            'It does not indicate the step in the RMA process; use operational state for that.'
        ),
    )
    state = fields.Selection(
        [
            ('received', _('Received')),
            ('review', _('In review')),
            ('repair', _('In repair')),
            ('stored', _('Stored')),
            ('shipped', _('Shipped')),
        ],
        string=_('Operational state'),
        default='received',
        tracking=True,
        help=_(
            'Where the unit is in the RMA workflow (reception, review, repair, storage, shipment). '
            'Independent of the physical condition of the item.'
        ),
    )
    received_date = fields.Datetime(string='Received Date')
    stored_date = fields.Datetime(string='Stored Date')
    shipped_date = fields.Datetime(string='Shipped Date')
    notes = fields.Text(string='Notes')
    harvest_notes = fields.Text(string='Harvesting Notes', help='Logs the spare parts harvested from this unit.')
    move_ids = fields.One2many('rma.unit.move', 'rma_unit_id', string='Moves')
    move_count = fields.Integer(compute='_compute_move_count', string='Move Count')

    @api.depends('move_ids')
    def _compute_move_count(self):
        for record in self:
            record.move_count = len(record.move_ids)
