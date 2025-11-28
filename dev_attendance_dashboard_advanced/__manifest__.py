# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2024 DaFe Solutions
#
##############################################################################

{
    'name': 'Attendance Dashboard Advanced | Employee Attendance Calendar',
    'category': 'Generic Modules/Human Resources',
    'version': '18.0.1.4',
    'author': 'DaFe Solutions',
    'maintainer': 'Programador 1, Programador 2',
    'description': """
        Employee Attendance Monthly Dashboard Odoo App, designed to revolutionize your attendance management. This intuitive app provides a comprehensive attendance dashboard where you can see employees with their job designations and day-wise attendance on one screen. The app displays check-in and check-out times along with the total hours worked each day. If an employee is on leave, it is clearly shown. For weekends, the app manages days off based on the employee's work schedule, and global holidays are also accounted for. If an employee does not have leave, weekend, attendance, or a holiday marked, they are displayed as absent for that day.

        The app features a flexible calendar that allows you to switch between months and years effortlessly. On the left side of the screen, you'll find a summary of monthly attendance, making attendance summary management straightforward. A unique feature is the ability to click on any holiday, leave, or attendance record to view detailed information. Filters for company, employee, month, and year make it easy to customize the data displayed to suit your needs.

        Additionally, the app provides a leave summary for the current month, which can be adjusted using the provided filters. This summary includes the employee's name, leave dates, and the reason for leave. A view button allows you to see detailed information about specific leave records. The Employee Attendance Monthly Dashboard Odoo App ensures efficient and straightforward attendance management, enhancing your organization's productivity.
    """,
    'summary': """
        Attendance Dashboard Employee Attendance Calendar Attendance Management Attendance Monthly Summary Attendance Report Attendance onscreen Leave Summary Employee Leave Screen Advanced Dashboard Monthwise Employee Attendance Report Excel PDF All in One Dashboard All in One Advanced Dashboard Advance Dashboard Odoo HRMS Dashboard All in One hrms Dashboard
    """,
    'depends': ['hr_attendance', 'hr_holidays'],
    'license': 'AGPL-3',
    'website': 'https://www.dafe.es',
    'data': [
        'security/security.xml',
        'report/extrahour_menu.xml',
        'report/extrahour_pdf_template.xml',
        'views/dashboard.xml',
        'views/attendance_calendar_view.xml',
        'views/hr_attendance.xml',
        'views/res_config_settings_view.xml',
        'views/hr_employee.xml',
    ],
    'assets': {
       'web.assets_backend': [
           'dev_attendance_dashboard_advanced/static/src/css/dashboard_new.css',
           'dev_attendance_dashboard_advanced/static/src/js/attendanceDashboard.js',
            'dev_attendance_dashboard_advanced/static/src/xml/attendance_dashboard.xml',
       ],
    },
    'images': ['static/description/icon.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
