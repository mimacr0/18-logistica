from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError
from collections import OrderedDict
from odoo.http import request


class PortalAttendance(CustomerPortal):

    @http.route(['/dashboard/attendance/<int:attendance_id>'], type='http', auth="public")
    def dashboard_my_attendance_detail(self, attendance_id, report_type=None, download=False, **kw):
        attendance_sudo = request.env['hr.employee'].sudo().browse(int(attendance_id))
        print("\n\n attendance_sudo>>",attendance_sudo)
        print("\n\n report_type>>",report_type)
        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=attendance_sudo, report_type=report_type, report_ref='dev_attendance_dashboard_advanced.action_report_extra_hours', download=download)

    
        	
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
