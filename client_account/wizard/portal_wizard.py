
from odoo import models, fields, api, Command, _
from odoo.exceptions import UserError


class PortalWizard(models.TransientModel):
    _inherit = 'portal.wizard'

    def _default_account_partner_ids(self):
        partner_ids = self.env.context.get('default_partner_ids', []) or self.env.context.get('active_ids', [])
        contact_ids = set()
        for partner in self.env['res.partner'].sudo().browse(partner_ids):
            contact_partners = partner.child_ids.filtered(lambda p: p.type in ('contact', 'other')) | partner
            contact_ids |= set(contact_partners.ids)

        for partner in self.env['res.partner'].sudo().browse(partner_ids):
            contact_ids = filter(lambda pid: pid != partner.id, contact_ids)

        return [Command.link(contact_id) for contact_id in contact_ids]

    partner_ids = fields.Many2many('res.partner', string='Partners', default=_default_account_partner_ids)

class PortalWizardUser(models.TransientModel):
    _inherit = 'portal.wizard.user'

    def action_grant_access(self):
        """
        Inherit the portal access granting method to add custom behavior
        for client account module
        """
        # Call the original method to maintain base functionality
        result = super(PortalWizardUser, self).action_grant_access()
        self.partner_id.parent_id._compute_portal_user_ids()
        return result

    def action_revoke_access(self):
        """
        Inherit the portal access revoking method to add custom behavior
        for client account module
        """
        # Call the original method to maintain base functionality
        result = super(PortalWizardUser, self).action_revoke_access()
        self.partner_id.parent_id._compute_portal_user_ids()
        return result
