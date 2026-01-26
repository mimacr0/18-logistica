from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class RepairTechnicianSetWizard(models.TransientModel):
    _name = 'repair.technician.set'
    _description = 'set Technician for Repair Order'

    technician_id = fields.Many2one(
        comodel_name='res.users',
        string='Technician',
        domain=lambda self: [('groups_id', 'in', [self.env.ref('logistics_security.group_repair_user').id, self.env.ref('logistics_security.group_repair_manager').id])]
    )
    repair_id = fields.Many2one('repair.order', string='Repair Order')
    repair_ids = fields.Many2many('repair.order', string='Repair Orders')

    def action_set_technician(self):
        if not self.technician_id:
            raise ValidationError(_('Please select a technician.'))
        repairs = self.repair_ids
        if not repairs and self.repair_id:
            repairs = self.repair_id
        if not repairs and self.env.context.get('active_ids'):
            repairs = self.env['repair.order'].browse(self.env.context.get('active_ids', []))
        if not repairs:
            raise ValidationError(_('No repair orders selected.'))

        now = fields.Datetime.now()
        repairs.write({
            'technician_id': self.technician_id.id,
            'assigned_user_id': self.technician_id.id,
            'assigned_date': now,
        })

        # Registrar en el chatter el cambio de técnico
        for repair in repairs:
            repair.message_post(
                body=_("Technician set to: %s") % self.technician_id.name,
                message_type='notification',
            )