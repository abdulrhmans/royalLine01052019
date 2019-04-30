# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import models


class Payslip(models.Model):
    
    _inherit = 'hr.employee'
    
    def get_work_days_data(self, from_datetime, to_datetime, calendar=None):
        data = self.get_attendance_data(from_datetime, to_datetime)
        return {
            'days': data['number_of_days'],
            'hours': data['number_of_hours'],
        }
    
    def get_attendance_data(self, from_datetime, to_datetime):
        total_wh = 0
        if to_datetime and from_datetime:
            from_date = from_datetime
            to_date = to_datetime
            attendences = {}
            employee = self
            sql = '''
            select att.worked_hours as worked_hours, att.check_in as checkin
            from hr_employee as emp inner join hr_attendance as att
                 on emp.id = att.employee_id
            where att.check_in >= %s and att.check_out <= %s and emp.id = %s
            order by checkin
            '''
            self.env.cr.execute(sql, (from_date, to_date, employee.id))
            attendences = self.env.cr.dictfetchall()
            wh = 0.0
            # sum up the attendances' durations
            dates_cal = []
            number_days = 0
            for att in attendences:
                dt = datetime.strptime(att['checkin'], '%Y-%m-%d %H:%M:%S')
                if dt.date() not in dates_cal:
                    dates_cal.append(dt.date())
                    number_days = number_days+1
                dur = att['worked_hours']
                if dur > 8:
                    wh += 8
                else:
                    wh += dur
            total_wh += wh
            
        return {'number_of_hours':total_wh , 'number_of_days':number_days}
    