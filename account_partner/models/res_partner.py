##############################################################################
#
# Copyright 2026 DaFe Solutions
#
##############################################################################
import re

from odoo import models, fields, api

class ResPartnerInh(models.Model):
    _inherit = 'res.partner'

    account = fields.Char(related='account_id.name', string='Account', size=9, readonly=True)
    account_id = fields.Many2one('account.partner', string='Account ID')
    type = fields.Selection(selection_add=[('sender', 'Sender')])
    is_carrier = fields.Boolean(string='Is Carrier')
    credits = fields.Float(string='Credit', compute='_compute_credits')
    sales = fields.Float(string='Sales', compute='_compute_sales')
    total_account = fields.Float(string='Total Account', compute='_compute_total_account')
    state_account = fields.Selection([('no', 'No Account'), ('new', 'Never Connected'), ('active', 'Confirmed')], default='no', string='State Account', compute='_compute_state_account')
    credit_account = fields.One2many(comodel_name='credit.account', inverse_name='partner_account')
    sale_order_ids = fields.Many2many(
        comodel_name='sale.order',
        relation='sale_order_user_rel',
        column1='partner_id',
        column2='order_id',
        string='Sale Orders',
        compute='_compute_sale_order_ids'
    )
    carrier_line_ids = fields.One2many(
        comodel_name='account.carrier.line',
        inverse_name='partner_id',
        string='Carrier Lines'
    )
    portal_user_ids = fields.Many2many(
        string='Users',
        comodel_name='res.partner',
        relation='res_partner_account_users_rel',
        column1='partner_id',
        column2='user_id',
        compute='_compute_portal_user_ids',
        store=True
    )

    contact_ids = fields.One2many(
        'res.partner',
        'parent_id',
        string='Contacts',
        domain=[('type', '=', 'contact')]
    )

    def check_portal_user_ids(self):
        self.ensure_one()
        self._compute_portal_user_ids()

    def _compute_portal_user_ids(self):
        for partner in self:
            partner.portal_user_ids = self.env['res.partner'].search([('parent_id', '=', partner.id), ('type', '=', 'contact'), ('user_ids', '!=', False)])

    @api.depends('portal_user_ids')
    def _compute_sale_order_ids(self):
        for partner in self:
            sale_orders = self.env['sale.order'].search([('partner_id.commercial_partner_id', '=', partner.commercial_partner_id.id)])
            partner.sale_order_ids = sale_orders

    @api.depends('portal_user_ids')
    def _compute_state_account(self):
        for record in self:
            if not record.portal_user_ids:
                record.state_account = 'no'
            else:
                state_user = self.env['res.users'].search([('partner_id', '=', record.id)], limit=1)
                if state_user and state_user.state == 'new':
                    record.state_account = 'new'
                else:
                    record.state_account = 'active'

    @api.depends('credit_account')
    def _compute_credits(self):
        for record in self:
            confirmed_amounts = record.credit_account.filtered(lambda a: a.state == 'confirmed').mapped('amount')
            record.credits = sum(confirmed_amounts)

    @api.depends('sale_order_ids')
    def _compute_sales(self):
        for record in self:
            confirmed_sales = record.sale_order_ids.filtered(lambda a: a.state == 'sale').mapped('amount_total')
            record.sales = sum(confirmed_sales)

    @api.depends('credits', 'sales')
    def _compute_total_account(self):
        for record in self:
            record.total_account = record.credits - record.sales

    ''' 
        This method is used to display the name of the partner in the views.
        Adding the logic to display only the name of the partner
        and not show the company name / parent name.
    '''
    @api.depends('complete_name', 'email', 'vat', 'state_id', 'country_id', 'commercial_company_name')
    @api.depends_context('show_address', 'partner_show_db_id', 'address_inline', 'show_email', 'show_vat', 'lang', 'hide_company_name')
    def _compute_display_name(self):
        for partner in self:
            super()._compute_display_name()
            if partner._context.get('hide_company_name'):
                search_text = partner.commercial_company_name + ', '
                partner.display_name = re.sub(search_text, '', partner.display_name)
