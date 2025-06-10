##############################################################################
#
# Copyright 2025 DaFe Solutions
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class RejectReasonCredit(models.TransientModel):
    _name = 'reject.reason.credit'
    _description = 'Reject Reason Credit'

    reason = fields.Text(string='Rejection Reason', required=True)

    def action_reject(self):
        active_id = self._context.get('active_id')
        if not active_id:
            raise ValidationError(_("No active ID found in context."))

        credit_account = self.env['credit.account'].browse(active_id)
        if credit_account:
            credit_account.state = 'rejected'
            credit_account.reject_reason = self.reason
            credit_account.reject_user = self.env.user.id
            credit_account.reject_date = fields.Datetime.now()
        else:
            raise ValidationError(_("Credit account not found."))