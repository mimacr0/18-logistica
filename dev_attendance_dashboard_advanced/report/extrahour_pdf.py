# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo import api, models


class AttendanceReport(models.AbstractModel):
    _name = 'report.dev_attendance_dashboard_advanced.overtime_pdf_template'

    def get_last_month_overtime(self):
        self.ensure_one()
        today = fields.Date.context_today(self)
        first_day_last_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        last_day_last_month = today.replace(day=1) - timedelta(days=1)

        return self.env['hr.attendance'].search([
            ('employee_id', '=', self.id),
            ('check_in', '>=', first_day_last_month),
            ('check_in', '<=', last_day_last_month),
            ('overtime', '>', 0)
        ])

    def _get_report_values(self, docids, data=None):
        docs = self.env['hr.employee'].browse(docids)
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.employee',
            'get_last_month_overtime': self.get_last_month_overtime,
            'docs': docs,
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
