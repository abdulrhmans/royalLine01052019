# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import time
from datetime import datetime
import calendar
from dateutil.relativedelta import relativedelta

class Contract(models.Model):
    _inherit = 'hr.contract'

    out_state = fields.Selection([('term', 'Termination'), ('resign', 'Resignation'), ], 'End of service Status')
    term_reason = fields.Selection([('probation','Termination During Probation'),
                                      ('perfomrance','Termination Due to Performance'),
                                      ('author','Termination According to Authorities'),
                                      ('discip','Termination Due to Disciplinary Actions'),
                                      ('medical','Termination Due to Medical Reasons'),
                                      ('retr','Retirement'),
                                      ('death','Death'),
                                      ('end_contract','End of Contract'),
                                      ('lay_off','Lay Off'),
                                      ('resign','Resignation')], 
                                      string='End Employment Reason')
    work_duration = fields.Float('Work Duration', digits=(12, 11), compute="_working_duration")
    work_duration_now = fields.Float('Work Duration (Untill Now)', digits=(12, 11), compute="_working_duration")
    
    realy_vacation = fields.Boolean('Relay Vacations', default=False)
    
    other_amount = fields.Float('')
    is_other = fields.Boolean('Provide Other Allowances')
    
    @api.one
    def _working_duration(self):
        total_years = 0.0
        total_years_now = 0.0
        if self.date_start and self.date_end:
            start = datetime.strptime(self.date_start, '%Y-%m-%d')
            end = datetime.strptime(self.date_end, '%Y-%m-%d')
            duration = relativedelta(end, start)
            years = duration.years
            total_months = duration.months
            total_days = duration.days
            months_to_years = 0.0
            days_to_years = 0.0
            if calendar.isleap(end.year):
                number_of_days_for_last_year = 366.0
            else:
                number_of_days_for_last_year = 365.0
                
            if total_months > 0:
                months_to_years = total_months/12.0
                
            if total_days > 0:
                days_to_years = total_days/number_of_days_for_last_year
            
            total_years = years+months_to_years+days_to_years
            
        if self.date_start:
            start = datetime.strptime(self.date_start, '%Y-%m-%d')
            end_now = datetime.strptime(time.strftime('%Y-%m-%d'), '%Y-%m-%d')
            duration_now = relativedelta(end_now, start)
            years_now = duration_now.years
            total_months_now = duration_now.months
            total_days_now = duration_now.days
            months_to_years_now = 0.0
            days_to_years_now = 0.0
            if calendar.isleap(end_now.year):
                number_of_days_for_last_year = 366.0
            else:
                number_of_days_for_last_year = 365.0
                
            if total_months_now > 0:
                months_to_years_now = total_months_now/12.0
                
            if total_days_now > 0:
                days_to_years_now = total_days_now/number_of_days_for_last_year
                 
            total_years_now = years_now+months_to_years_now+days_to_years_now
            
        self.work_duration = total_years
        self.work_duration_now = total_years_now
            
    def get_unpaid_leaves(self):
        leaves = self.env['hr.holidays']
        # number_of_days_temp
        number_unpaid_days = 0.0
        if self.employee_id:
            leaves_rec = leaves.search([('type','=','remove'), ('employee_id','=', self.employee_id.id),('state','=','validate'),
                                         ('holiday_status_id.unpaid','=', True) ])
            for leave in leaves_rec:
                number_unpaid_days += leave.number_of_days_temp
        
        return int(number_unpaid_days)
    
