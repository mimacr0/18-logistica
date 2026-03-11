# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2026 DaFe Solutions
#
##############################################################################

from odoo import models, fields, api, _


class RmaUnit(models.Model):
    _name = 'rma.unit'
    _description = 'RMA Unit'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('RMA...')) == _('RMA...'):
                vals['name'] = self.env['ir.sequence'].next_by_code('rma.unit.sequence') or _('RMA...')
                
        records = super().create(vals_list)
        for record in records:
            if record.location_id:
                self.env['rma.unit.move'].create({
                    'rma_unit_id': record.id,
                    'from_location_id': False,
                    'to_location_id': record.location_id.id,
                    'user_id': self.env.uid,
                    'date': fields.Datetime.now(),
                    'reason': _('Initial Reception'),
                })
        return records

    def write(self, vals):
        if 'location_id' in vals:
            for record in self:
                if record.location_id.id != vals['location_id']:
                    self.env['rma.unit.move'].create({
                        'rma_unit_id': record.id,
                        'from_location_id': record.location_id.id,
                        'to_location_id': vals['location_id'],
                        'user_id': self.env.uid,
                        'date': fields.Datetime.now(),
                        'reason': _('Location Updated'),
                    })
        return super().write(vals)
    
    name = fields.Char(
        string="RMA Number",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _("RMA...")
    )
    active = fields.Boolean(default=True, string="Active")
    product_id = fields.Many2one(
        "product.product",
        required=True,
        string="Product"
    )
    owner_id = fields.Many2one(
        "res.partner",
        required=True,
        string="Owner",
        tracking=True
    )
    #Aún se esta desarrollando por parte de otros programadores.
    # client_product_map_id = fields.Many2one(
    #     "client.product.map",
    #     string="Client Product Map"
    # )
    package_id = fields.Many2one(
        "stock.quant.package",
        string="Package"
    )
    location_id = fields.Many2one(
        "stock.location",
        index=True,
        string="Location",
        tracking=True
    )
    serial = fields.Char(index=True, string="Serial")
    imei = fields.Char(index=True, string="IMEI")
    condition = fields.Selection([
        ("E", "On hold"),
        ("A","New"),
        ("B","Used"),
        ("C","Repair"),
        ("D","Discard")
    ], string="Condition", tracking=True)
    state = fields.Selection([
        ("received","Received"),
        ("inspection","Inspection"),
        ("waiting_customer","Waiting Customer"),
        ("repair","Repair"),
        ("refurbish","Refurbish"),
        ("stored","Stored"),
        ("ready_to_ship","Ready to ship"),
        ("shipped","Shipped"),
        ("scrap","Scrap"),
        ("use_for_spare_parts", "Use for Spare Parts")
    ], string="State", tracking=True)
    received_date = fields.Datetime(string="Received Date")
    stored_date = fields.Datetime(string="Stored Date")
    shipped_date = fields.Datetime(string="Shipped Date")
    notes = fields.Text(string="Notes")
    move_ids = fields.One2many(
        "rma.unit.move",
        "rma_unit_id",
        string="Moves"
    )
    move_count = fields.Integer(
        compute="_compute_move_count",
        string="Move Count"
    )

    @api.depends("move_ids")
    def _compute_move_count(self):
        for record in self:
            record.move_count = len(record.move_ids)