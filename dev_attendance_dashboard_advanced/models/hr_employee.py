# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo import models, fields, api, _

class hr_employee(models.Model):
    _inherit = 'hr.employee'

    allowed_companies = fields.Many2many('res.company', string="Allowed Companies", compute='_compute_companies', store=True)

    def _compute_companies(self):
        print("============================================")
        # for record in self:
        #     record.allowed_companies = self._context.get('allowed_company_ids')
        #     print(record.allowed_companies)
        
#    def get_last_month_overtime(self):
#        self.ensure_one()
#        today = fields.Date.context_today(self)
#        first_day_last_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
#        last_day_last_month = today.replace(day=1) - timedelta(days=1)

#        return self.env['hr.attendance'].search([
#            ('employee_id', '=', self.id),
#            ('check_in', '>=', first_day_last_month),
#            ('check_in', '<=', last_day_last_month),
#            ('overtime', '>', 0)
#        ])
    
    
        
        
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
