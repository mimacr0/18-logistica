from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """Inherit res_config_settings model for adding some fields in Settings"""
    _inherit = 'res.config.settings'

    allowed_entry_time_float = fields.Float(
        string='Allowed Entry Time (Float)',
        default=9.5,  # 9:30 AM = 9.5 horas
        help='Hora límite de entrada permitida en formato decimal (ej: 9.5 = 9:30 AM)'
    )

    minor_delay_limit_float = fields.Float(
        string='Minor Delay Limit (Float)',
        default=10.0,  # 10:00 AM = 10.0 horas
        help='Límite de retraso menor en formato decimal (ej: 10.0 = 10:00 AM)'
    )

    major_delay_limit_float = fields.Float(
        string='Major Delay Limit (Float)',
        default=10.5,  # 10:30 AM = 10.5 horas
        help='Límite de retraso mayor en formato decimal (ej: 10.5 = 10:30 AM)'
    )

    delay_by_check_in = fields.Boolean(
        string='Delay Depends on Check-In Time',
        default=True,
        help='Si está activado, las horas de retraso se calculan basándose en la hora de entrada (check_in)'
    )

    # Guardar los valores
    def set_values(self):
        super().set_values()
        params = self.env['ir.config_parameter'].sudo()
        # Guardar valores Float
        params.set_param('attendance.allowed_entry_time_float', str(self.allowed_entry_time_float) if self.allowed_entry_time_float else '')
        
        # Si delay_by_check_in está activado, calcular los límites basándose en allowed_entry_time_float
        if self.delay_by_check_in:
            # Minor delay = allowed_entry + 0.5 horas
            minor_delay_calculated = self.allowed_entry_time_float + 0.5
            # Major delay = allowed_entry + 1.0 horas
            major_delay_calculated = self.allowed_entry_time_float + 1.0
            params.set_param('attendance.minor_delay_limit_float', str(minor_delay_calculated))
            params.set_param('attendance.major_delay_limit_float', str(major_delay_calculated))
        else:
            # Usar los valores configurados manualmente
            params.set_param('attendance.minor_delay_limit_float', str(self.minor_delay_limit_float) if self.minor_delay_limit_float else '')
            params.set_param('attendance.major_delay_limit_float', str(self.major_delay_limit_float) if self.major_delay_limit_float else '')
        
        # Guardar campo booleano
        params.set_param('attendance.delay_by_check_in', str(self.delay_by_check_in) if self.delay_by_check_in else 'False')

    # Leer los valores al abrir la vista
    @api.model
    def get_values(self):
        res = super().get_values()
        params = self.env['ir.config_parameter'].sudo()

        # Leer valores Float
        allowed_entry_time_float_str = params.get_param('attendance.allowed_entry_time_float')
        minor_delay_limit_float_str = params.get_param('attendance.minor_delay_limit_float')
        major_delay_limit_float_str = params.get_param('attendance.major_delay_limit_float')
        # Leer campo booleano
        delay_by_check_in_str = params.get_param('attendance.delay_by_check_in', 'True')
        delay_by_check_in = delay_by_check_in_str.lower() == 'true' if delay_by_check_in_str else True

        # Convertir a float
        allowed_entry_time_float = float(allowed_entry_time_float_str) if allowed_entry_time_float_str else 9.5
        
        # Si delay_by_check_in está activado, calcular los límites basándose en allowed_entry_time_float
        if delay_by_check_in:
            minor_delay_limit_float = allowed_entry_time_float + 0.5
            major_delay_limit_float = allowed_entry_time_float + 1.0
        else:
            minor_delay_limit_float = float(minor_delay_limit_float_str) if minor_delay_limit_float_str else 10.0
            major_delay_limit_float = float(major_delay_limit_float_str) if major_delay_limit_float_str else 10.5

        res.update(
            allowed_entry_time_float=allowed_entry_time_float,
            minor_delay_limit_float=minor_delay_limit_float,
            major_delay_limit_float=major_delay_limit_float,
            delay_by_check_in=delay_by_check_in,
        )
        return res


