# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2026 DaFe Solutions
#
##############################################################################

from odoo import models, fields, api

class AddAccountPartner(models.TransientModel):
    _name = 'add.account.partner'
    _description = 'Add Account Partner'

    partner_id = fields.Many2one('res.partner', string='Contact')
    account = fields.Char(string='Account', size=9)
    commercial = fields.Many2one('res.users', string='Commercial', default=lambda self: self.env.user)
    lang = fields.Selection(related='partner_id.lang', string='Language', readonly=False)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.lang = False

    def add_account(self):
        # Crear un nuevo registro en account.partner
        account_partner = self.env['account.partner'].create({
            'name': self.account.upper(),
            'partner_id': self.partner_id.id,
        })
        # Asignar el registro creado al campo account_id del partner
        self.partner_id.account_id = account_partner.id
        self.partner_id.user_id = self.commercial.id
        # Retornar la acción para mostrar los partners con cuenta
        action = self.sudo().env.ref('account_partner.action_partner_account')
        return action.read()[0]