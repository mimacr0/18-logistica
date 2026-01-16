from odoo import fields, models, api, _
from datetime import time
from pytz import timezone
import pytz


class HrAttendance(models.Model):
    """ Adds field to show delay status on hr_attendance """
    _inherit = 'hr.attendance'

    delay_status = fields.Selection([
            ('on_time', 'On Time'),
            ('minor', 'Minor Delay'),
            ('unjustified_abs', 'Unjustified Absence'),
            ('justified_abs', 'Justified Absence'),
        ], string='Delay Status', compute='_compute_delay_status_float', store=True)

    def action_recalculate_delay_status(self):
        """
        Server action to recalculate delay_status for selected attendances.
        Can be called from tree view action or form view button.
        """
        if self:
            self._compute_delay_status_float()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Recalculation Complete'),
                'message': _('%d attendance(s) recalculated.') % len(self),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_recalculate_all_delay_status(self):
        """
        Server action to recalculate delay_status for ALL attendances.
        """
        all_attendances = self.search([])
        if all_attendances:
            all_attendances._compute_delay_status_float()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Recalculation Complete'),
                'message': _('%d attendance(s) recalculated.') % len(all_attendances),
                'type': 'success',
                'sticky': False,
            }
        }

    def _float_to_time(self, hour_float):
        """Convert float hour to time object (e.g., 9.5 = 9:30)"""
        hour_int = int(hour_float)
        minute_int = int((hour_float - hour_int) * 60)
        return time(hour_int, minute_int)

    def _get_employee_calendar(self, employee=None):
        """Get the resource calendar for an employee (from contract or employee).
        
        If employee is not provided, uses self.employee_id (for compatibility with base hr_attendance).
        """
        if employee is None:
            employee = self.employee_id
        if not employee:
            return None
        return employee.contract_id.resource_calendar_id or employee.resource_calendar_id

    def _get_delay_settings(self, employee):
        """
        Get delay settings from employee's resource calendar.
        
        Returns: (allowed_entry_float, minor_delay_float) or (None, None) if not configured
        """
        calendar = self._get_employee_calendar(employee)
        if calendar and calendar.allowed_entry_time and calendar.minor_delay_limit:
            return calendar.allowed_entry_time, calendar.minor_delay_limit
        return None, None

    def _get_leave_for_date(self, employee, check_in_date):
        """Get approved leave for employee on a specific date"""
        if not employee:
            return None
        return self.env['hr.leave'].sudo().search([
            ('employee_id', '=', employee.id),
            ('request_date_from', '<=', check_in_date),
            ('request_date_to', '>=', check_in_date),
            ('state', '=', 'validate'),
        ], limit=1, order='id desc')

    @api.depends('check_in')
    def _compute_delay_status_float(self):
        for record in self:
            if not record.check_in:
                record.delay_status = False
                continue

            employee = record.employee_id
            
            # Get delay settings from resource calendar
            allowed_entry_float, minor_delay_float = record._get_delay_settings(employee)
            
            # If no settings configured, skip delay calculation
            if not allowed_entry_float or not minor_delay_float:
                record.delay_status = False
                continue

            # Get timezone from calendar
            calendar = record._get_employee_calendar(employee)
            tz_name = (calendar.tz if calendar else None) or (employee.tz if employee else None) or self.env.user.tz or 'UTC'
            
            # Convert check_in from UTC to employee's timezone
            tz = timezone(tz_name)
            check_in_utc = pytz.utc.localize(record.check_in) if record.check_in.tzinfo is None else record.check_in.astimezone(pytz.utc)
            check_in_local = check_in_utc.astimezone(tz)
            check_in_time = check_in_local.time()
            check_in_date = check_in_local.date()

            # Default times from calendar
            allowed_time = record._float_to_time(allowed_entry_float)
            minor_time = record._float_to_time(minor_delay_float)

            # Check for leave that modifies entry time
            leave = record._get_leave_for_date(employee, check_in_date)
            if leave:
                # Check if it's hourly leave or morning half-day
                if leave.request_unit_hours and leave.request_hour_to:
                    allowed_time = record._float_to_time(leave.request_hour_to)
                    minor_time = record._float_to_time(leave.request_hour_to + 0.5)
                elif leave.request_unit_half and leave.request_date_from_period == 'am' and leave.request_hour_to:
                    allowed_time = record._float_to_time(leave.request_hour_to)
                    minor_time = record._float_to_time(leave.request_hour_to + 0.5)

            # Compare times and set status
            if check_in_time <= allowed_time:
                record.delay_status = 'on_time'
            elif check_in_time < minor_time:
                record.delay_status = 'minor'
            else:
                record.delay_status = 'unjustified_abs'
