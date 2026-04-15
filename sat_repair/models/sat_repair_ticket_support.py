# -*- coding: utf-8 -*-
from random import randint

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

from .sat_repair_choices import TYPE_RMA_REPAIR_CATEGORY


class RmaRepairTicketType(models.Model):
    _name = 'rma.repair.ticket.type'
    _description = 'RMA Repair Ticket Type'
    _order = 'sequence, name'

    name = fields.Char(string='Name', required=True, translate=True)
    description = fields.Text(string='Description', translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(default=True)
    color = fields.Integer(string='Color')
    sequence_id = fields.Many2one('ir.sequence', string='Numbering sequence', ondelete='restrict')
    sequence_prefix = fields.Char(string='Sequence Prefix', size=5)


class RmaRepairTicketCategory(models.Model):
    _name = 'rma.repair.ticket.category'
    _description = 'RMA Repair Ticket Category'
    _order = 'sequence, name'
    _parent_name = 'parent_id'
    _parent_store = True
    _rec_name = 'complete_name'

    name = fields.Char(string='Name', required=True, translate=True, index=True)
    complete_name = fields.Char(
        string='Complete Name',
        compute='_compute_complete_name',
        recursive=True,
        store=True,
    )
    parent_id = fields.Many2one(
        'rma.repair.ticket.category',
        string='Parent Category',
        index=True,
        ondelete='cascade',
        domain="[('id', '!=', id)]",
    )
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many(
        'rma.repair.ticket.category',
        'parent_id',
        string='Subcategories',
    )
    description = fields.Text(string='Description', translate=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(string='Sequence', default=10)
    color = fields.Integer(string='Color', default=0)
    type_category = fields.Selection(TYPE_RMA_REPAIR_CATEGORY, string='Type Category')
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        ondelete='cascade',
    )

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = f'{category.parent_id.complete_name} / {category.name}'
            else:
                category.complete_name = category.name

    @api.constrains('parent_id')
    def _check_category_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('Error: Cannot create recursive categories.'))

    def name_get(self):
        result = []
        for category in self:
            result.append((category.id, category.complete_name or category.name))
        return result


class RmaRepairTicketTag(models.Model):
    _name = 'rma.repair.ticket.tag'
    _description = 'RMA Repair Ticket Tag'
    _order = 'name'

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char(string='Name', required=True, translate=True)
    color = fields.Integer(string='Color', default=_get_default_color)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('rma_repair_ticket_tag_name_uniq', 'unique (name)', 'Tag name must be unique!')
    ]
