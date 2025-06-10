
from odoo import models, fields, api, _
from datetime import datetime

class AccountPartner(models.Model):
    _inherit = 'account.partner'

    reception_sequence = fields.Integer(string='Reception Sequence', copy=False, default=1)

    def _increase_reception_sequence(self):
        for record in self:
            record.reception_sequence += 1
    
    @api.model
    def _get_reception_sequence(self, name):
        # Obtener el nombre de la empresa
        # company_name = self.env.user.company_id.name
        # Obtener la fecha actual en formato YY-MM-DD
        date_str = datetime.now().strftime('%Y%m%d')
        # Obtener la secuencia numérica
        sequence_number = self.env['ir.sequence'].next_by_code('stock.reception.sequence')
        # Formatear el nombre
        return f"{name}{date_str}{sequence_number}"

    @api.model
    def _restart_reception_sequence(self):
        for record in self:
            record.reception_sequence = 1