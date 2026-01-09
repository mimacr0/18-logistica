from odoo import models, fields, api, _

class RepairTechnicianSetWizard(models.TransientModel):
    _name = 'repair.technician.set'
    _description = 'set Technician for Repair Order'

    technician_id = fields.Many2one(
        comodel_name='res.users',
        string='Technician',
        domain=lambda self: [('groups_id', 'in', [self.env.ref('logistics_security.group_repair_user').id, self.env.ref('logistics_security.group_repair_manager').id])]
    )
    repair_id = fields.Many2one('repair.order', string='Repair Order')

    def action_set_technician(self):
        if not self.technician_id:
            raise ValidationError(_('Please select a technician.'))
        self.repair_id.technician_id = self.technician_id
        self.repair_id.assigned_user_id = self.technician_id
        self.repair_id.assigned_date = fields.Datetime.now()

        # Registrar en el chatter el cambio de técnico
        self.repair_id.message_post(
            body=_("Technician set to: %s") % self.technician_id.name,
            message_type='notification',
        )