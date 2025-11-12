# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################
from odoo import fields, models, api
from datetime import time


class HrAttendance(models.Model):
    """ Adds field to show delay status on hr_attendance """
    _inherit = 'hr.attendance'

    delay_status = fields.Selection([
            ('on_time', 'On Time'),
            ('minor', 'Minor Delay'),
            ('major', 'Major Delay'),
            ('absent', 'Absent'),
        ], string='Delay Status', compute='_compute_delay_status_float', store=True)

    @api.depends('check_in')
    def _compute_delay_status_float(self):
        params = self.env['ir.config_parameter'].sudo()

        # Leer los valores de configuración como float (ya calculados en settings)
        allowed_entry_float_str = params.get_param('attendance.allowed_entry_time_float')
        minor_delay_float_str = params.get_param('attendance.minor_delay_limit_float')
        major_delay_float_str = params.get_param('attendance.major_delay_limit_float')

        # Convertir strings a float
        allowed_entry_float = float(allowed_entry_float_str) if allowed_entry_float_str else 9.5
        minor_delay_float = float(minor_delay_float_str) if minor_delay_float_str else 10.0
        major_delay_float = float(major_delay_float_str) if major_delay_float_str else 10.5

        # Convertir float a time (ej: 9.5 = 9:30)
        def float_to_time(hour_float):
            hour_int = int(hour_float)
            minute_int = int((hour_float - hour_int) * 60)
            return time(hour_int, minute_int)

        allowed_time_default = float_to_time(allowed_entry_float)
        minor_time_default = float_to_time(minor_delay_float)
        major_time_default = float_to_time(major_delay_float)

        for record in self:
            if not record.check_in:
                record.delay_status = False
                continue

            check_in_time = record.check_in.time()  # Hora del empleado
            check_in_date = record.check_in.date()  # Fecha de la asistencia

            # Buscar si hay un permiso (hr.leave) para este empleado y fecha
            allowed_time = None
            if record.employee_id:
                leave = self.env['hr.leave'].sudo().search([
                    ('employee_id', '=', record.employee_id.id),
                    ('request_date_from', '<=', check_in_date),
                    ('request_date_to', '>=', check_in_date),
                    ('state', '=', 'validate'),
                ], limit=1, order='id desc')
                
                if leave:
                    # Verificar si es permiso por horas o de medio día por la mañana
                    if leave.request_unit_hours and leave.request_hour_to:
                        # Convertir Float a time (ej: 10.5 = 10:30)
                        hour_to_int = int(leave.request_hour_to)
                        minute_to_int = int((leave.request_hour_to - hour_to_int) * 60)
                        allowed_time = time(hour_to_int, minute_to_int)
                    elif leave.request_unit_half and leave.request_date_from_period == 'am' and leave.request_hour_to:
                        # Medio día por la mañana: usar request_hour_to
                        hour_to_int = int(leave.request_hour_to)
                        minute_to_int = int((leave.request_hour_to - hour_to_int) * 60)
                        allowed_time = time(hour_to_int, minute_to_int)

            # Si no hay permiso o no aplica, usar la configuración por defecto
            if allowed_time is None:
                allowed_time = allowed_time_default
                minor_time = minor_time_default
                major_time = major_time_default
            else:
                # Si hay permiso que cambia la hora de entrada, recalcular los límites basándose en esa hora
                # Leer el campo booleano para saber si debemos recalcular
                delay_by_check_in_str = params.get_param('attendance.delay_by_check_in', 'True')
                delay_by_check_in = delay_by_check_in_str.lower() == 'true' if delay_by_check_in_str else True
                
                if delay_by_check_in:
                    # Convertir allowed_time a float para hacer los cálculos
                    allowed_hour_float = allowed_time.hour + (allowed_time.minute / 60.0)
                    # Minor delay = allowed_time + 0.5 horas
                    minor_hour_float = allowed_hour_float + 0.5
                    # Major delay = allowed_time + 1.0 horas
                    major_hour_float = allowed_hour_float + 1.0
                    # Convertir de vuelta a time
                    minor_time = float_to_time(minor_hour_float)
                    major_time = float_to_time(major_hour_float)
                else:
                    # Usar los valores configurados manualmente
                    minor_time = minor_time_default
                    major_time = major_time_default

            # Comparar directamente horas y minutos
            if check_in_time <= allowed_time:
                record.delay_status = 'on_time'
            # Si llega entre la hora de inicio y el límite de retraso menor: retraso leve
            elif allowed_time <= check_in_time < minor_time:
                record.delay_status = 'minor'
            # Si llega entre el límite menor y el mayor: retraso grave
            elif minor_time <= check_in_time < major_time:
                record.delay_status = 'major'
            # Si llega después del límite mayor: ausente
            else:
                record.delay_status = 'absent'

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

