# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from dateutil import relativedelta
from datetime import time as datetime_time


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    @api.one
    def get_paid_unpaid_days(self, worked_days):
        paid_days = 0.0
        unpaid_days = 0.0
        for l in worked_days.dict:
            line = worked_days.dict[l]
            if line.leave_type_id:
                if line.leave_type_id.unpaid:
                    unpaid_days += line.number_of_days
                else:
                    paid_days += line.number_of_days
            else:
                paid_days += line.number_of_days
            
        return [paid_days, unpaid_days]
    
    @api.one
    def get_paid_unpaid_hours(self, worked_days):
        paid_hours = 0.0
        unpaid_hours = 0.0
        for l in worked_days.dict:
            line = worked_days.dict[l]
            if line.leave_type_id:
                if line.leave_type_id.unpaid:
                    unpaid_hours += line.number_of_hours
                else:
                    paid_hours += line.number_of_hours
            else:
                paid_hours += line.number_of_hours
            
        return [paid_hours, unpaid_hours]


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    
    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        """
        @param contract: Browse record of contracts
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """
        res = super(HrPayslip, self).get_worked_day_lines(contracts, date_from, date_to)
        result = []
        for line in res:
            if line['code'] != 'WORK100':
                leave_rec = self.env['hr.holidays.status'].search(['|',('code', '=', line['code']),
                                                                   ('name', '=', line['code'])])
                if leave_rec:
                    line['leave_type_id'] = leave_rec[0].id
                    line['code'] = leave_rec[0].code
            
            result.append(line)
                
        return result
#         res = []
#         # fill only if the contract as a working schedule linked
#         for contract in contracts.filtered(lambda contract: contract.resource_calendar_id):
#             day_from = datetime.combine(fields.Date.from_string(date_from), datetime_time.min)
#             day_to = datetime.combine(fields.Date.from_string(date_to), datetime_time.max)
# 
#             # compute leave days
#             leaves = {}
#             day_leave_intervals = contract.employee_id.iter_leaves(day_from, day_to, calendar=contract.resource_calendar_id)
#             break_duration = 0.0
#             if hasattr(contract.resource_calendar_id, 'break_duration'):
#                 break_duration = contract.resource_calendar_id.break_duration
#             for day_intervals in day_leave_intervals:
#                 for interval in day_intervals:
#                     holiday = interval[2]['leaves'].holiday_id
#                     current_leave_struct = leaves.setdefault(holiday.holiday_status_id, {
#                         'name': holiday.holiday_status_id.name,
#                         'sequence': 5,
#                         'code': holiday.holiday_status_id.name,
#                         'number_of_days': 0.0,
#                         'number_of_hours': 0.0,
#                         'contract_id': contract.id,
#                         'leave_type_id': holiday.holiday_status_id.id,
#                     })
#                     leave_time = ((interval[1] - interval[0]).seconds / 3600) - break_duration
#                     current_leave_struct['number_of_hours'] += leave_time
#                     work_hours = contract.employee_id.get_day_work_hours_count(interval[0].date(), calendar=contract.resource_calendar_id)
#                     current_leave_struct['number_of_days'] += leave_time / work_hours
# 
#             # compute worked days
#             work_data = contract.employee_id.get_work_days_data(day_from, day_to, calendar=contract.resource_calendar_id)
#             attendances = {
#                 'name': _("Normal Working Days paid at 100%"),
#                 'sequence': 1,
#                 'code': 'WORK100',
#                 'number_of_days': work_data['days'],
#                 'number_of_hours': work_data['hours'],
#                 'contract_id': contract.id,
#             }
# 
#             res.append(attendances)
#             res.extend(leaves.values())
#         return res
    

class hr_payslip_worked_days(models.Model):
    _inherit = 'hr.payslip.worked_days'
    
    leave_type_id = fields.Many2one('hr.holidays.status','Leave Type')
    