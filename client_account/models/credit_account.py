##############################################################################
#
# Copyright 2025 DaFe Solutions
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CreditAccount(models.Model):
    _name = 'credit.account'
    _description = 'Credit Account'

    account_id = fields.Many2one('account.partner', string='Account')
    partner_account = fields.Many2one('res.partner', string='Partner Account', compute='_compute_partner_account', store=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', "New") == "New":
                vals['name'] = self.env['ir.sequence'].next_by_code('credit.account') or _("New")
        return super(CreditAccount, self).create(vals_list)

    name = fields.Char(string='Name', copy=False, default='New')
    date = fields.Date(string='Date', default=fields.Date.context_today)
    amount = fields.Float(string='Amount', default='')
    currency_id = fields.Many2one(related='partner_account.currency_id', string='Currency')
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed'), ('rejected', 'Rejected')], string='State', default='draft')
    concept = fields.Selection([('transfer', 'Bank Transfer'), ('cash', 'Cash Payment'), ('credit', 'Monthly Credit')], string='Concept')
    approve_user = fields.Many2one('res.users', string='Approved By')
    approve_date = fields.Datetime(string='Approved Date')
    reject_user = fields.Many2one('res.users', string='Rejected By')
    reject_date = fields.Datetime(string='Rejected Date')
    reject_reason = fields.Text(string='Rejection Reason')

    @api.constrains('amount')
    def _check_amount(self):
        for record in self:
            if record.amount <= 0:
                raise ValidationError(_("Entering an amount is required."))

    @api.depends('account_id')
    def _compute_partner_account(self):
        for record in self:
            record.partner_account = record.account_id.partner_id

    def action_confirm(self):
        for record in self:
            if record.state == 'draft':
                record.state = 'confirmed'
                record.approve_user = self.env.user.id
                record.approve_date = fields.Datetime.now()
            else:
                raise ValidationError(_("This record is already confirmed."))

    def return_to_draft(self):
        for record in self:
            if record.state == 'rejected':
                record.state = 'draft'
                record.approve_user = False
                record.approve_date = False
            else:
                raise ValidationError(_("This record is already in draft state."))