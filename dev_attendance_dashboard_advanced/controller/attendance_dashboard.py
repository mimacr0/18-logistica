# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################
import datetime
from datetime import date,timedelta
from odoo import http
from odoo.http import request
import math, calendar
import pytz
from calendar import monthrange
import io
import xlsxwriter
import base64
import logging

_logger = logging.getLogger(__name__)


class AttendanceDashboard(http.Controller):
    
    @http.route('/attendance/report/download', type='http', auth='user')
    def download_attendance_report(self, **kwargs):
        request_data = kwargs
        domains = self.roomDashboardFilterApply({'request': request_data})
        employee_domain = domains.get('employee_domain', [])
        department_domain = domains.get('department_domain', [])
        month = int(domains.get('month_domain') or datetime.date.today().month)
        year = int(domains.get('year_domain') or datetime.date.today().year)

        employee_name = "All"
        department_name = "All"
        if employee_domain:
            emp_id = employee_domain[0][2]
            employee_name = request.env['hr.employee'].browse(emp_id).name
        if department_domain:
            dept_id = department_domain[0][2]
            department_name = request.env['hr.department'].browse(dept_id).name

        employee_ids = request.env['hr.employee'].search(employee_domain + department_domain)
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet('Attendance Report')

        # Formats
        bold = workbook.add_format({'bold': True, 'align': 'center'})
        center_format = workbook.add_format({'align': 'center'})
        header_format = workbook.add_format({'align': 'center',  'bold': True})
        present_format = workbook.add_format({'bg_color': 'green', 'align': 'center','border': 1})
        absent_format = workbook.add_format({'bg_color': '#f27f74', 'align': 'center','border': 1})
        leave_format = workbook.add_format({'bg_color': '#f7bb59', 'align': 'center','border': 1})
        weekend_format = workbook.add_format({'bg_color': '#e0dfdc', 'align': 'center','border': 1})
        holiday_format = workbook.add_format({'bg_color': '#a2bbf5', 'align': 'center','border': 1})
        minor_delay_format = workbook.add_format({'bg_color': '#ffeb3b', 'align': 'center','border': 1})
        major_delay_format = workbook.add_format({'bg_color': '#ff9800', 'align': 'center','border': 1})

        # Filters info
        sheet.write('A1', 'Employee', bold)
        sheet.write('B1', employee_name,center_format)
        sheet.write('A2', 'Department', bold)
        sheet.write('B2', department_name,center_format)
        sheet.write('A3', 'Month', bold)
        sheet.write('B3', calendar.month_name[month],center_format)
        sheet.write('A4', 'Year', bold)
        sheet.write('B4', str(year),center_format)

        bold_wrap = workbook.add_format({'bold': True,'bg_color': '#a1a2a6'})
        sheet.write('D1', '[W-Weekend]', bold_wrap)
        sheet.write('D2', '[P-Present]', bold_wrap)
        sheet.write('D3', '[A-Absent]', bold_wrap)
        sheet.write('D4', '[H-Holiday]', bold_wrap)
        sheet.write('D5', '[L-Leave]', bold_wrap)
        sheet.write('D6', '[MD-Minor Delay]', bold_wrap)
        sheet.write('D7', '[GD-Major Delay]', bold_wrap)
        
        sheet.write('A7', 'Seq.', bold)
        sheet.write('B7', 'Employee', bold)

        # Set column widths
        sheet.set_column('A:A', 15)
        sheet.set_column('B:B', 20)
        sheet.set_column('C:C', 15)

        # Header row: Date - Day
        days = calendar.monthrange(year, month)[1]
        start_col = 2
        for day in range(1, days + 1):
            date = datetime.date(year, month, day)
            weekday = calendar.day_name[date.weekday()][:3].upper()
            col = start_col + day - 1
            sheet.write(6, col, f'{date.strftime("%d/%m/%Y")} - {weekday}', header_format)
            sheet.set_column(col, col, 20, center_format)

        # Employee data
        row = 7
        seq = 1
        for employee in employee_ids:
            sheet.write(row, 0, seq,center_format)
            sheet.write(row, 1, employee.name,center_format)

            for day in range(1, days + 1):
                date = datetime.datetime(year, month, day)
                check_in = date.replace(hour=0, minute=0, second=1)
                check_out = date.replace(hour=23, minute=59, second=59)
                weekday = date.weekday()

                # Check if weekend
                workdays = [int(wd.dayofweek) for wd in employee.resource_calendar_id.attendance_ids]
                is_weekend = weekday not in workdays

                # Check public holiday
                is_holiday = any(
                    h.date_from.date() <= date.date() <= h.date_to.date()
                    for h in employee.resource_calendar_id.global_leave_ids
                )

                col = start_col + day - 1

                leave_ids = request.env['hr.leave'].search([
                    ('employee_id', '=', employee.id),
                    ('request_date_from', '<=', check_in.date()),
                    ('request_date_to', '>=', check_out.date()),
                    ('state', '=', 'validate')
                ])

                # Check attendance
                attendance_ids = request.env['hr.attendance'].search([
                    ('employee_id', '=', employee.id),
                    ('check_in', '>=', check_in),
                    ('check_out', '<=', check_out)
                ])

                if is_holiday:
                    sheet.write(row, col, 'H', holiday_format)
                elif leave_ids:
                    sheet.write(row, col, 'L', leave_format)
                elif attendance_ids:
                    total_seconds = 0
                    delay_status = None
                    for att in attendance_ids:
                        if att.check_in and att.check_out:
                            total_seconds += (att.check_out - att.check_in).total_seconds()
                        # Obtener delay_status de la primera asistencia
                        if delay_status is None and att.delay_status:
                            delay_status = att.delay_status

                    hours = int(total_seconds // 3600)
                    minutes = int((total_seconds % 3600) // 60)
                    hours_worked = f"{hours:02}:{minutes:02}"

                    # Determinar formato según delay_status
                    cell_format = present_format
                    status_prefix = 'P'
                    if delay_status == 'minor':
                        cell_format = minor_delay_format
                        status_prefix = 'MD'
                    elif delay_status == 'major':
                        cell_format = major_delay_format
                        status_prefix = 'GD'

                    if hours > 0 or minutes > 0:
                        sheet.write(row, col, f"{status_prefix} {hours_worked}", cell_format)
                    else:
                        sheet.write(row, col, status_prefix, cell_format)
                elif is_weekend:
                    sheet.write(row, col, 'W', weekend_format)
                else:
                    sheet.write(row, col, 'A', absent_format)

            row += 1
            seq += 1

        workbook.close()
        output.seek(0)
        return request.make_response(output.read(), [
            ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Disposition', 'attachment; filename=attendance_report.xlsx')
        ])

    
    @http.route('/send_attendance_email', type='json', auth='user')
    def send_attendance_email(self, data=None, **kwargs):
        try:
            request_data = kwargs
            domains = self.roomDashboardFilterApply({'request': request_data})
            employee_domain = domains.get('employee_domain', [])
            department_domain = domains.get('department_domain', [])
            month = int(domains.get('month_domain') or datetime.date.today().month)
            year = int(domains.get('year_domain') or datetime.date.today().year)
            days_in_month = calendar.monthrange(year, month)[1]

            employees = request.env['hr.employee'].search(employee_domain + department_domain)

            if not employees:
                return {'success': False, 'message': 'No matching employees found.'}

            local = pytz.timezone(request.env.user.tz or 'UTC')

            for employee in employees:
                summary = {'p': 0, 'a': 0, 'l': 0, 'W': 0, 'h': 0, 'md': 0, 'gd': 0}
                attendance_table_rows = ""
                public_holidays = employee.resource_calendar_id.global_leave_ids
                working_days = [int(x.dayofweek) for x in employee.resource_calendar_id.attendance_ids]

                for day in range(1, days_in_month + 1):
                    dt_in = datetime.datetime(year, month, day, 0, 0, 1)
                    dt_out = datetime.datetime(year, month, day, 23, 59, 59)
                    date_str = dt_in.strftime("%d %b - %A")

                    status = "-"
                    details = "-"
                    color = "black"
                    holiday_found = False

                    # Check for holidays
                    for holiday in public_holidays:
                        from_date = holiday.date_from.astimezone(local).date()
                        to_date = holiday.date_to.astimezone(local).date()
                        if from_date <= dt_in.date() <= to_date:
                            status = "Holiday"
                            details = holiday.name or "Public Holiday"
                            color = "blue"
                            summary['h'] += 1
                            holiday_found = True
                            break

                    if holiday_found:
                        pass
                    else:
                        leave = request.env['hr.leave'].search([
                            ('employee_id', '=', employee.id),
                            ('request_date_from', '<=', dt_in.date()),
                            ('request_date_to', '>=', dt_out.date()),
                            ('state', '=', 'validate')
                        ], limit=1)

                        attendance = request.env['hr.attendance'].search([
                            ('employee_id', '=', employee.id),
                            ('check_in', '>=', dt_in),
                            ('check_out', '<=', dt_out),
                        ], limit=1)

                        if leave:
                            status = "Leave"
                            details = leave.holiday_status_id.name or "Leave"
                            color = "orange"
                            summary['l'] += 1
                        elif attendance:
                            worked_hours = attendance.worked_hours or 0
                            hours = int(worked_hours)
                            minutes = int((worked_hours - hours) * 60)
                            
                            # Verificar delay_status
                            delay_status = attendance.delay_status or 'on_time'
                            if delay_status == 'minor':
                                status = "Present (Minor Delay)"
                                color = "#ffeb3b"
                            elif delay_status == 'major':
                                status = "Present (Major Delay)"
                                color = "#ff9800"
                            else:
                                status = "Present"
                                color = "green"
                            
                            details = f"{hours} hour{'s' if hours != 1 else ''} {minutes} minute{'s' if minutes != 1 else ''}"
                            summary['p'] += 1
                            if delay_status == 'minor':
                                summary['md'] += 1
                            elif delay_status == 'major':
                                summary['gd'] += 1
                        elif dt_in.weekday() not in working_days:
                            status = "Week Off"
                            details = "-"
                            color = "gray"
                            summary['W'] += 1
                        else:
                            status = "Absent"
                            details = "-"
                            color = "red"
                            summary['a'] += 1

                    attendance_table_rows += f"""
                        <tr>
                            <td style="text-align:center;">{date_str}</td>
                            <td style="color:{color}; font-weight:bold; text-align:center;">{status}</td>
                            <td style="text-align:center;">{details}</td>
                        </tr>
                    """

                
                email_body = f"""
                    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #2c3e50; padding: 20px;">

                        <h2 style="background-color: #4A90E2; color: white; text-align: center; padding: 15px; border-radius: 8px;">
                            Monthly Attendance Report
                        </h2>

                        <div style="background-color: #f7f9fc; border: 1px solid #dcdfe6; border-radius: 8px; padding: 15px; margin-top: 20px;">
                            <p><strong> Employee:</strong> {employee.name}</p>
                            <p><strong> Month:</strong> {calendar.month_name[month]} {year}</p>
                            <p><strong> Job Position:</strong> {employee.job_id.name or 'N/A'}</p>
                            <p><strong> Department:</strong> {employee.department_id.name or 'N/A'}</p>
                        </div>

                        <h3 style="color: #4A90E2; margin-top: 30px;"> Summary</h3>
                        <table border='1' style="width: 100%; border-collapse: collapse; margin-bottom: 20px; text-align: center;">
                            <thead style="background-color: #e9eff7;">
                                <tr>
                                    <th style="padding: 8px;">Present</th>
                                    <th style="padding: 8px;">Absent</th>
                                    <th style="padding: 8px;">Leave</th>
                                    <th style="padding: 8px;">Week Off</th>
                                    <th style="padding: 8px;">Holiday</th>
                                    <th style="padding: 8px;">Minor Delay</th>
                                    <th style="padding: 8px;">Major Delay</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td style="padding: 8px;">{summary['p']}</td>
                                    <td style="padding: 8px;">{summary['a']}</td>
                                    <td style="padding: 8px;">{summary['l']}</td>
                                    <td style="padding: 8px;">{summary['W']}</td>
                                    <td style="padding: 8px;">{summary['h']}</td>
                                    <td style="padding: 8px;">{summary.get('md', 0)}</td>
                                    <td style="padding: 8px;">{summary.get('gd', 0)}</td>
                                </tr>
                            </tbody>
                        </table>

                        <h3 style="color: #4A90E2; margin-top: 30px;"> Daily Attendance</h3>
                        <table border='1' cellpadding='9' cellspacing='0' style='border-collapse: collapse; width: 100%; font-size: 14px;'>
                            <thead style="background-color: #e9eff7;">
                                <tr>
                                    <th style="width: 33%; text-align: center;">Date</th>
                                    <th style="width: 33%; text-align: center;">Status</th>
                                    <th style="width: 34%; text-align: center;">Details</th>
                                </tr>
                            </thead>
                            <tbody>
                                {attendance_table_rows}
                            </tbody>
                        </table>

                    </div>
                    """

                if employee.work_email:
                    request.env['mail.mail'].sudo().create({
                        'subject': f"Attendance Report - {calendar.month_name[month]} {year}",
                        'email_to': employee.work_email,
                        'body_html': email_body,
                    }).send()

                    employee.message_post(
                        body=f"Attendance report for {calendar.month_name[month]} {year} sent to {employee.work_email}.",
                        subject="Attendance Report Sent",
                        message_type='notification',
                        subtype_xmlid='mail.mt_note'
                    )

            return {'success': True}

        except Exception as e:
            _logger.exception("Error in send_attendance_email")
            return {'success': False, 'message': str(e)}

    

    
    @http.route('/employee/attendance', auth='public', type='json')
    def employee_attendance(self, **kw):
        user_tz = request.env.user.tz or pytz.utc  # Get user's timezone or default to UTC
        local = pytz.timezone(user_tz)
        employee_domain = []
        month_domain = datetime.date.today().month
        year_domain = datetime.date.today().year
        department_domain = []
        domains = self.roomDashboardFilterApply(kw)

        if domains:
            if domains['employee_domain']:
                employee_domain = domains['employee_domain']

            if domains['department_domain']:
                department_domain = domains['department_domain']

            if domains['month_domain']:
                month_domain = domains['month_domain']

            if domains['year_domain']:
                year_domain = domains['year_domain']

        response = [[]]
        employee_ids = request.env['hr.employee'].search(employee_domain + department_domain)

        days = calendar.monthrange(year_domain, month_domain)[1]

        for employee in employee_ids:
            emp_dict = {}
            att_dict = {}
            all_leaves = []
            all_present = []
            all_holidays = []
            leave = 0
            absent = 0
            present = 0
            weekoff = 0
            t_holiday = 0
            minor_delay = 0
            major_delay = 0
            emp_dict['id'] = employee.id

            if employee.image_1920 and len(employee.image_1920) > 1000:
                emp_dict['img'] = employee.image_1920
            else:
                emp_dict['img'] = None
            emp_dict['name'] = employee.name
            emp_dict['job'] = employee.job_id.name

            for day in range(1,days+1):
                check_in = datetime.datetime(year_domain, month_domain, day, 00, 00, 1)
                check_out = datetime.datetime(year_domain, month_domain, day, 23, 59, 59)
                employee_work_schedule = employee.resource_calendar_id.attendance_ids
                workingdays = list(set([int(schedule.dayofweek) for schedule in employee_work_schedule]))

                public_holiday_ids = employee.resource_calendar_id.global_leave_ids
                
                # Verificar primero si es holiday
                is_holiday = False
                holiday_id = None
                for holiday in public_holiday_ids:
                    from_date = holiday.date_from.astimezone(local).date()
                    to_date = holiday.date_to.astimezone(local).date()
                    if from_date <= check_in.date() <= to_date:
                        is_holiday = True
                        holiday_id = holiday.id
                        break

                if check_in.weekday() not in workingdays:
                    # Buscar asistencias que tengan check_in en el día, incluso si no tienen check_out
                    attendance_ids = request.env['hr.attendance'].search([
                        ('employee_id', 'in', [employee.id]), 
                        ('check_in', '>=', check_in), 
                        ('check_in', '<=', check_out)
                    ], order='id asc') 
                    if attendance_ids:
                        for att in attendance_ids.ids:
                            all_present.append(att)
                        # Calcular horas trabajadas, manejando el caso cuando no hay check_out
                        total_hours = 0
                        for att in attendance_ids:
                            if att.worked_hours:
                                total_hours += att.worked_hours
                            elif att.check_in and not att.check_out:
                                # Si hay check_in pero no check_out, calcular hasta el final del día
                                day_end = check_out
                                total_hours += (day_end - att.check_in).total_seconds() / 3600.0
                        
                        td = timedelta(hours=total_hours)
                        hours, remainder = divmod(td.total_seconds(), 3600)
                        minutes = remainder // 60
                        
                        # Obtener delay_status de la primera asistencia del día
                        delay_status = attendance_ids[0].delay_status if attendance_ids[0].delay_status else 'on_time'
                        att_dict[day] = {
                            'status': 'p', 
                            'hours': '{:02}:{:02}'.format(int(hours), int(minutes)),
                            'ids': attendance_ids.ids,
                            'delay_status': delay_status
                        }
                        present+=1
                        if delay_status == 'minor':
                            minor_delay += 1
                        elif delay_status == 'major':
                            major_delay += 1
                    else:
                        att_dict[day] = {'status':'W'}
                        weekoff+=1

                else:
                    # Si es holiday, marcarlo como holiday (tiene prioridad sobre leave y absent)
                    if is_holiday:
                        att_dict[day] = {'status':'holiday', 'ids':holiday_id}
                        all_holidays.append(holiday_id)
                        t_holiday += 1
                    else:
                        leave_ids = request.env['hr.leave'].search([('employee_id', 'in', [employee.id]), ('request_date_from', '<=', check_in.date()), ('request_date_to', '>=', check_out.date()),('state', 'in', ['validate'])])
                        
                        if leave_ids:
                            all_leaves.append(leave_ids.id)
                            if leave_ids.request_unit_half or leave_ids.request_unit_hours:
                                total_hours = leave_ids.number_of_hours
                                td = timedelta(hours=total_hours)
                                hours, remainder = divmod(td.total_seconds(), 3600)
                                minutes = remainder // 60
                                att_dict[day] = {'status':'l', 'hours': '{:02}:{:02} H'.format(int(hours), int(minutes)), 'ids': leave_ids.id}
                            else:
                                att_dict[day] = {'status':'l', 'hours': 'L', 'ids': leave_ids.id}

                            leave+=1
                        else:
                            # Buscar asistencias que tengan check_in en el día, incluso si no tienen check_out
                            attendance_ids = request.env['hr.attendance'].search([
                                ('employee_id', 'in', [employee.id]), 
                                ('check_in', '>=', check_in), 
                                ('check_in', '<=', check_out)
                            ], order='id asc')
                            if attendance_ids:
                                for att in attendance_ids.ids:
                                    all_present.append(att)
                                # Calcular horas trabajadas, manejando el caso cuando no hay check_out
                                total_hours = 0
                                for att in attendance_ids:
                                    if att.worked_hours:
                                        total_hours += att.worked_hours
                                    elif att.check_in and not att.check_out:
                                        # Si hay check_in pero no check_out, calcular hasta el final del día
                                        day_end = check_out
                                        total_hours += (day_end - att.check_in).total_seconds() / 3600.0
                                
                                td = timedelta(hours=total_hours)
                                hours, remainder = divmod(td.total_seconds(), 3600)
                                minutes = remainder // 60
                                
                                # Obtener delay_status de la primera asistencia del día
                                delay_status = attendance_ids[0].delay_status if attendance_ids[0].delay_status else 'on_time'
                                att_dict[day] = {
                                    'status': 'p', 
                                    'hours': '{:02}:{:02}'.format(int(hours), int(minutes)),
                                    'ids': attendance_ids.ids,
                                    'delay_status': delay_status
                                }
                                present+=1
                                if delay_status == 'minor':
                                    minor_delay += 1
                                elif delay_status == 'major':
                                    major_delay += 1
                            else:
                                att_dict[day] = {'status':'absent'}
                                absent+=1

            emp_dict['attendance'] = att_dict
            if all_leaves:
                emp_dict['all_leave'] = list(set(all_leaves))
            if all_present:
                emp_dict['all_present'] = all_present
            if all_holidays:
                emp_dict['all_holidays'] = all_holidays
            emp_dict['summary'] = {'w':weekoff, 'l':leave, 'p':present, 'a':absent-t_holiday, 'h':t_holiday, 'md':minor_delay, 'gd':major_delay}
            response[0].append(emp_dict)
        response.append({'days':days})
        return response
        
        
    '''        
        [{'id': 6, 
          'name': 'Abigail Peterson', 
          'img' : 'img',
          'leave_ids' : [leave ids],
          'all_leave' : [all leave]
          'job_id': (3, 'Consultant'),
          'attendance':{
              1 : 'Absent'
              2 : 8.36}
        }, {days:}]
          '''
    
    
    @http.route('/employee/leave', auth='public', type='json')
    def get_leave_detail(self, **kw):
        domains = self.roomDashboardFilterApply(kw)
        employee_domain = []
        department_filter_id = None
        month_domain = datetime.datetime.today().month
        year_domain = datetime.datetime.today().year

        if domains:
            if domains['employee_domain']:
                emp_ids = domains['employee_domain'][0][2]
                emp_ids = [emp_ids] if isinstance(emp_ids, int) else emp_ids
                employee_domain = [('employee_id', 'in', emp_ids)]

            if domains['month_domain']:
                month_domain = domains['month_domain']

            if domains['year_domain']:
                year_domain = domains['year_domain']

            if domains['department_domain']:
                department_filter_id = domains['department_domain'][0][2]

        leaves = request.env['hr.leave'].search_read(
            employee_domain + [('state', '=', 'validate')],
            ['employee_id', 'holiday_status_id', 'request_date_from', 'request_date_to', 'duration_display', 'name','state'],
            order='request_date_from asc'
        )

        new_leave_details = []
        for leave in leaves:
            leave_month = leave['request_date_from'].month
            leave_year = leave['request_date_from'].year
            if leave_month == month_domain and leave_year == year_domain:
                if department_filter_id:
                    emp = request.env['hr.employee'].browse(leave['employee_id'][0])
                    if emp.department_id.id == department_filter_id:
                        new_leave_details.append(leave)
                else:
                    new_leave_details.append(leave)
        return new_leave_details
    
    
    
    @http.route('/render_attendance_dashboard_filter', auth='user', type='json')
    def renderAttendanceDashboardFilter(self):
        user = request.env.user
        employee_ids = []
        department_ids = []

        is_admin = user.has_group('base.group_system')

        if is_admin:
            employee_ids = request.env['hr.employee'].sudo().search_read([], ['id', 'name'])
            department_ids = request.env['hr.department'].sudo().search_read([], ['id', 'name'])
        else:
            current_employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)

            if current_employee and current_employee.department_id:
                dept = current_employee.department_id
                employee_ids = request.env['hr.employee'].sudo().search_read([('department_id', '=', dept.id)],['id', 'name'])
                department_ids = [{'id': dept.id, 'name': dept.name}]
        
        return [employee_ids, department_ids]

    
    @http.route('/get_employees_by_department', auth='user', type='json')
    def getEmployeesByDepartment(self, department_id=None):
        user = request.env.user
        is_admin = user.has_group('base.group_system')

        # Get current employee
        current_employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        allowed_dept_id = current_employee.department_id.id if current_employee else False

        # Default to empty result
        domain = [('id', '=', -1)]

        if is_admin:
            if department_id and department_id != 'all':
                domain = [('department_id', '=', int(department_id))]
            elif department_id == 'all':
                domain = []  # all employees
        else:
            if department_id and department_id != 'all':
                # Allow only their department
                if int(department_id) == allowed_dept_id:
                    domain = [('department_id', '=', allowed_dept_id)]
            else:
                # Even if user tries "all", restrict to only their department
                if allowed_dept_id:
                    domain = [('department_id', '=', allowed_dept_id)]

        employees = request.env['hr.employee'].sudo().search_read(domain, ['id', 'name'])
        return employees
    

    @http.route('/attn/user_detail', auth='public', type='json')
    def hotel_user_detail(self):
        user_name = request.env.user.name
        user_img = request.env.user.image_1920

        if user_img and len(user_img) > 1000:
            final_user_img = request.env.user.image_1920
        else:
            final_user_img = False

        return {
            'user_img': final_user_img,
            'user_name': user_name
        }

    # ================counters==============
    @http.route('/get/attendance/tiles/data', auth='public', type='json')
    def get_tiles_data(self, **kw):
        user_tz = request.env.user.tz or pytz.utc
        local = pytz.timezone(user_tz)

        # Get filters
        domains = self.roomDashboardFilterApply(kw)

        # Fallback to current date if no filter
        today = date.today()
        month = domains.get('month_domain') or today.month
        # month = domains.get('month_domain') or datetime.date.today().month
        # year = domains.get('year_domain') or datetime.date.today().year
        year = domains.get('year_domain') or today.year

        start_date = date(year, month, 1)
        end_date = date(year, month, monthrange(year, month)[1])

        employee_domain = domains.get('employee_domain', [])
        department_domain = domains.get('department_domain', [])

        all_present = []
        all_absent = []
        on_leave = []
        late_checkin = []
        
        # Contadores para el día actual
        all_present_today = []
        all_absent_today = []
        on_leave_today = []
        late_checkin_today = []
        
        # Fecha de hoy en la zona horaria del usuario
        now_utc = pytz.utc.localize(datetime.datetime.utcnow())
        now_local = now_utc.astimezone(local)
        today_date = now_local.date()
        # Convertir a datetime con timezone
        today_start = local.localize(datetime.datetime.combine(today_date, datetime.datetime.min.time()))
        today_end = local.localize(datetime.datetime.combine(today_date, datetime.datetime.max.time()))
        # Convertir a UTC para la búsqueda en la base de datos
        today_start_utc = today_start.astimezone(pytz.utc).replace(tzinfo=None)
        today_end_utc = today_end.astimezone(pytz.utc).replace(tzinfo=None)

        all_employee_data = request.env['hr.employee'].search(employee_domain + department_domain)

        for employee in all_employee_data:
            # Attendance in filtered month
            attendances = request.env['hr.attendance'].search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', start_date),
                ('check_in', '<=', end_date)
            ], order='check_in asc')

            if attendances:
                # Buscar asistencias con retraso (minor o major)
                late_attendances = attendances.filtered(
                    lambda a: a.delay_status in ('minor', 'major')
                )
                if late_attendances and employee.id not in late_checkin:
                    late_checkin.append(employee.id)
                
                all_present.append(employee.id)
            else:
                # Check for leave
                leaves = request.env['hr.leave'].search([
                    ('employee_id', '=', employee.id),
                    ('request_date_from', '<=', end_date),
                    ('request_date_to', '>=', start_date),
                    ('state', '=', 'validate'),
                ])
                if leaves:
                    on_leave.append(employee.id)
                else:
                    all_absent.append(employee.id)
            
            # Cálculo para el día actual
            attendances_today = request.env['hr.attendance'].search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', today_start_utc),
                ('check_in', '<=', today_end_utc)
            ], order='check_in asc')
            
            if attendances_today:
                # Buscar asistencias con retraso (minor o major) para hoy
                late_attendances_today = attendances_today.filtered(
                    lambda a: a.delay_status in ('minor', 'major')
                )
                if late_attendances_today and employee.id not in late_checkin_today:
                    late_checkin_today.append(employee.id)
                
                all_present_today.append(employee.id)
            else:
                # Check for leave today
                leaves_today = request.env['hr.leave'].search([
                    ('employee_id', '=', employee.id),
                    ('request_date_from', '<=', today_date),
                    ('request_date_to', '>=', today_date),
                    ('state', '=', 'validate'),
                ])
                if leaves_today:
                    on_leave_today.append(employee.id)
                else:
                    all_absent_today.append(employee.id)

        return {
            'all_employee_data': all_employee_data.ids,
            'all_present': all_present,
            'all_absent': all_absent,
            'on_leave': on_leave,
            'late_checkin': late_checkin,
            # Contadores para el día actual
            'all_present_today': all_present_today,
            'all_absent_today': all_absent_today,
            'on_leave_today': on_leave_today,
            'late_checkin_today': late_checkin_today
        }


    @http.route('/attendance_dashboard_filter_apply', auth='public', type='json')
    def roomDashboardFilterApply(self, kw):

        request_data = kw.get('request', {}) if kw else {}

        employee_domain = []
        department_domain = []
        month_domain = None
        year_domain = None

        user = request.env.user
        user_department = user.employee_id.department_id

        is_admin = user.has_group('base.group_system')  

        # Employee filter
        employee_id = request_data.get('employee')
        if employee_id and employee_id != "all":
            employee_id = int(employee_id)
            employee_domain = [('id', '=', employee_id)]

        # Department filter
        department_id = request_data.get('department')
        if department_id and department_id != "all":
            department_id = int(department_id)
            department_domain = [('department_id', '=', department_id)]
        else:
            if not is_admin:
                # If user is not admin, restrict to their own department
                if user_department:
                    department_domain = [('department_id', '=', user_department.id)]
            else:
                # Admin can see all departments (leave department_domain empty)
                department_domain = []

        # Month filter
        month = request_data.get('month')
        if month:
            month_domain = int(month) + 1  

        # Year filter
        year = request_data.get('year')
        if year:
            year_domain = int(year)

        return {
            'employee_domain': employee_domain,
            'department_domain': department_domain,
            'month_domain': month_domain,
            'year_domain': year_domain
        }

    

    

    
    
